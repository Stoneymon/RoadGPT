import click
import importlib
import traceback
import time
import os
import sys
import errno
import logging as log
import csv

import matplotlib
matplotlib.use('Agg')

from dotenv import load_dotenv

from roadgpt.road_generator import RoadGenerator, RoadRegenerator

from code_pipeline.beamng_executor import BeamngExecutor
from code_pipeline.visualization import RoadTestVisualizer
from code_pipeline.tests_generation import TestGenerationStatistic
from code_pipeline.test_generation_utils import register_exit_fun

from code_pipeline.tests_evaluation import OOBAnalyzer

OUTPUT_RESULTS_TO = 'results'
MAP_SIZE = 1000
OOB_TOLERANCE = 0.95
SPEED_LIMIT = 70
# Sentinel values
ANY = object()
ANY_NOT_NONE = object()
DEFAULT = object()


def create_experiment_description(result_folder, params_dict):
    log.info("Creating Experiment Description")
    experiment_description_file = os.path.join(result_folder, "experiment_description.csv")
    csv_columns = params_dict.keys()
    try:
        with open(experiment_description_file, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()
            writer.writerow(params_dict)
            log.info("Experiment Description available: %s", experiment_description_file)
    except IOError:
        log.error("I/O error. Cannot write Experiment Description")


def create_summary(result_folder, raw_data):
    log.info("Creating Reports")

    # Refactor this
    if type(raw_data) is TestGenerationStatistic:
        log.info("Creating Test Statistics Report:")
        summary_file = os.path.join(result_folder, "generation_stats.csv")
        csv_content = raw_data.as_csv()
        with open(summary_file, 'w') as output_file:
            output_file.write(csv_content)
        log.info("Test Statistics Report available: %s", summary_file)

    log.info("Creating OOB Report")
    oobAnalyzer = OOBAnalyzer(result_folder)
    oob_summary_file = os.path.join(result_folder, "oob_stats.csv")
    csv_content = oobAnalyzer.create_summary()
    with open(oob_summary_file, 'w') as output_file:
        output_file.write(csv_content)

    log.info("OOB  Report available: %s", oob_summary_file)

def post_process(ctx, result_folder, the_executor):
    """
        This method is invoked once the test generation is over.
    """
    # Plot the stats on the console
    log.info("Test Generation Statistics:")
    log.info(the_executor.get_stats())

    # Generate the actual summary files
    create_experiment_description(result_folder, ctx.params)

    # Generate the other reports
    create_summary(result_folder, the_executor.get_stats())

def create_post_processing_hook(ctx, result_folder, executor):
    """
        Uses HighOrder functions to setup the post processing hooks that will be trigger ONLY AND ONLY IF the
        test generation has been killed by us, i.e., this will not trigger if the user presses Ctrl-C

    :param result_folder:
    :param executor:
    :return:
    """

    def _f():
        if executor.is_force_timeout():
            # The process killed itself because a timeout, so we need to ensure the post_process function
            # is called
            post_process(ctx, result_folder, executor)

    return _f

def get_script_path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))

@click.command()
@click.option('--beamng-home', required=False, default=None, type=click.Path(exists=True),
              show_default='None',
              help="Customize BeamNG executor by specifying the home of the simulator.")
@click.option('--beamng-user', required=False, default=None, type=click.Path(exists=True),
              show_default='Currently Active User (~/BeamNG.tech/)',
              help="Customize BeamNG executor by specifying the location of the folder "
                   "where levels, props, and other BeamNG-related data will be copied."
                   "** Use this to avoid spaces in URL/PATHS! **")
@click.option('--model', required=False, type=click.Choice(["assistant", "chatgpt"], case_sensitive=False), default="chatgpt")
# @click.option('--prompt', required=True, default=None, type=str)
# @click.option('--repetitions', required=False, default=1, type=int,
#               help="Number of times roads are generated with the given prompt.")
@click.pass_context
def generate(ctx, beamng_home, beamng_user, model):
    ctx.ensure_object(dict)
    # TODO Refactor by adding a create summary command and forwarding the output of this run to that command

    road_visualizer = None
    # Setup visualization
    road_visualizer = RoadTestVisualizer(map_size=MAP_SIZE)

    # Setup folder structure by ensuring that the basic folder structure is there.
    default_output_folder = os.path.join(get_script_path(), OUTPUT_RESULTS_TO)
    try:
        os.makedirs(default_output_folder)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    
    if model == "assistant":
        from roadgpt.roadgpt_classes import RoadGPTAssistant
        roadgpt = RoadGPTAssistant()
    elif model == "chatgpt":
        from roadgpt.roadgpt_classes import RoadGPT
        roadgpt = RoadGPT()
    prompt = input("Your road description: ")
    while prompt != "exit":
        # Create the unique folder that will host the results of this execution using the test generator data and
        # a timestamp as id
        # TODO Allow to specify a location for this folder and the run id
        timestamp_id = time.time() * 100000000 // 1000000
        result_folder = os.path.join(default_output_folder,
                                    "_".join([str("roadgpt"), str("RoadGPT"), str(timestamp_id)]))

        try:
            os.makedirs(result_folder)
        except OSError:
            log.fatal("An error occurred during test generation")
            traceback.print_exc()
            sys.exit(2)
        

        # log.info("Outputting results to " + result_folder)
        executor = BeamngExecutor(result_folder, MAP_SIZE, oob_tolerance=OOB_TOLERANCE, max_speed_in_kmh=SPEED_LIMIT,
                                    beamng_home=beamng_home, beamng_user=beamng_user, road_visualizer=road_visualizer)
        # Register the shutdown hook for post processing results

        register_exit_fun(create_post_processing_hook(ctx, result_folder, executor))
        repetitions = int(input("How many times do you want to create a road with that prompt? "))
        for i in range(repetitions):
            response = roadgpt.prompt(prompt)
            index = response.find('{')
            response = response[index:]
            print(response)
            try:
                segment_dict = eval(response)
                print(segment_dict)
            except:
                print("ChatGPT returned the wrong file type")
                continue
            starting_point = segment_dict["starting_point"]
            del segment_dict["starting_point"]
            theta = segment_dict["theta"]
            del segment_dict["theta"]

            generator = RoadGenerator(starting_point, theta, segment_dict)
            generator.translate_to_nodes()
            try:
                # Start the generation
                generator.start(executor)
            except Exception:
                log.fatal("An error occurred during test generation")
                traceback.print_exc()
                sys.exit(2)
            finally:
                # Ensure the executor is stopped no matter what.
                # TODO Consider using a ContextManager: With executor ... do
                executor.close()
        prompt=input("Road description")

    # We still need this here to post process the results if the execution takes the regular flow
    post_process(ctx, result_folder, executor)


if __name__=="__main__":
    generate()