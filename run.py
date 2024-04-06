from code_pipeline.beamng_executor import BeamngExecutor
from code_pipeline.visualization import RoadTestVisualizer
from roadgpt.roadgpt import RoadGPT
from roadgpt.road_generator import RoadGenerator
from beamngpy import BeamNGpy, Scenario, Vehicle

OUTPUT_RESULTS_TO = "results"

roadgpt = RoadGPT()
road_description = "Create a mountain road with serpentines."

response = roadgpt.prompt(road_description)
print(response)
segment_dict = eval(response)
# try:
#     print(segment_dict)
# except Exception as e:
#     print("Error:", e)

segments = segment_dict.keys()
print(segment_dict)
segments = sorted(segments)
segments.remove("starting_point")
print(segments)

generator = RoadGenerator(segment_dict["starting_point"])



for segment in segments:
    next_node = generator.calculate_next_node(segment_dict[segment]["turn_degrees"], segment_dict[segment]["distance"], segment_dict[segment]["incline"])
    print(next_node)

# interpolated_road = generator.interpolate_road(generator.nodes)

result_folder = "./results"
map_size=250
road_visualizer = RoadTestVisualizer(map_size=map_size)

executor = BeamngExecutor(result_folder, map_size,
                            oob_tolerance=0.9, max_speed_in_kmh=70,
                            beamng_home="C:\BeamNG.tech\BeamNG.tech.v0.26.2.0", beamng_user="C:\BeamNG.tech_user",
                            road_visualizer=road_visualizer)
generator.start(executor)