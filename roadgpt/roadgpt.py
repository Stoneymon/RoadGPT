from dotenv import load_dotenv, set_key
from openai import OpenAI
import os
import time

# load_dotenv(os.path.join(os.getcwd(), '..', '.env'))

class RoadGPT:

    def __init__(self):
        print("RoadGPT init")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.assistant_id = os.getenv("ROADGPT_ID")
        self.client = OpenAI(api_key=self.openai_api_key)

        # if not os.getenv("ROADGPT_ID"):
        # self.assistant_id = self.create_assistant("RoadGPT")
            # set_key(".env", "ROADGPT_ID", self.assistant_id)

        self.threads = []
        self.runs = []

    @classmethod
    def create_assistant(self, name):
        print("RoadGPT create_assistant")
        roadgpt = self.client.beta.assistants.create(
            name = name,
            instructions = """
            You are a road designer, who designs roads to test the lane keeping functionality of self driving vehicles.
            People give you descriptions of roads and you create more detailed descriptions of novel roads, where you split the road into segments. 
            
            Here are some ground rules:
            - Each turn / straight is it's own segment.
            - Every change in incline is it's own segment.
            - For every segment return the distance of the end point of the segment to the end point of the previous segment in meters, direction (e.g. right turn), the incline in % and the degrees of the turn in case it is a turn.
            - Only return "left", "right" or "straight" for the direction
            - Only return numbers for the distance, incline and the degrees of the turn.
            - Write declines in height and the degrees of left turns as negative numbers.
            - The maximum incline is 15% and the road is not allowed to be self intersecting. 
            - Return the road description in json format of {'road_segment1': {'distance': int, 'direction': str, 'incline': int, 'turn_degrees': int}, 'road_segment2': {'distance': int, 'direction': str, 'incline': int, 'turn_degrees': int}}, etc.""",
            model = "gpt-3.5-turbo"
        )
        set_key(".env", "ROADGPT_ID", self.assistant_id)

        return roadgpt.id
    
    
    def create_thread(self):
        print("RoadGPT create_thread")
        thread = self.client.beta.threads.create()
        self.threads.append(thread.id)

        return thread.id
    

    def create_run(self, thread_id):
        print("RoadGPT create_run")
        run = self.client.beta.threads.runs.create(
            thread_id = thread_id,
            assistant_id = self.assistant_id
        )

        self.runs.append(run)

        return run
    

    def wait_on_run(self, run, thread_id):
        print("RoadGPT wait_on_run")
        while run.status == "queued" or run.status == "in_progress":
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id,
            )
            time.sleep(0.5)
        return run
    

    def prompt(self, prompt):
        print("RoadGPT prompt")
        thread_id = self.create_thread()

        message = self.client.beta.threads.messages.create(
            thread_id = thread_id,
            role = "user",
            content = prompt
        )

        run = self.create_run(thread_id)
        run = self.wait_on_run(run, thread_id)

        messages = self.client.beta.threads.messages.list(thread_id=thread_id)
        response = messages.data[0].content[0].text.value

        return response
    


if __name__ == "__main__":
    roadgpt = RoadGPT()
    road_description = "Create a mountain road with serpentines."

    response = roadgpt.prompt(road_description)
    print(response)
    print(type(response))
    try:
        dictionary = eval(response)
        print(dictionary)
        print(type(dictionary))
    except Exception as e:
        print("Error:", e)
    # print(os.getcwd())