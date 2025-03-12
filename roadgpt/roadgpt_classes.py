from dotenv import load_dotenv, set_key
from openai import OpenAI
import os
import time

openai_api_key = load_dotenv(os.path.join(os.getcwd(), '..', '.env'))

class RoadGPTAssistant:

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.assistant_id = os.getenv("ROADGPT_ID")
        if not self.assistant_id:
            self.assistant_id = self.create_assistant()

        # if not os.getenv("ROADGPT_ID"):
        # self.assistant_id = self.create_assistant("RoadGPT")
            # set_key(".env", "ROADGPT_ID", self.assistant_id)

        self.threads = []
        self.runs = []

    def create_assistant(self, name):
        roadgpt = self.client.beta.assistants.create(
            name = name,
            instructions = """
            You are a road designer, who designs roads to test the lane keeping functionality of self driving vehicles. People give you descriptions of roads and you create more detailed descriptions of novel roads, where you split the road into segments. These descriptions are then turned into coordinates, so keep the coordinate values in mind. Since you are testing the lane keeping functionality of self driving vehicles, you want to stress it.

            Here are some ground rules:
            - The roads should be diverse, that means given the same description don't create the same road (Start in different directions, etc.)
            - The car should cover as many directions on the map as possible / The car should face as many directions as possible while using your road.
            - before the first segment give me a starting point (x, y, z), consider your starting point when you build the road since the x and y values are not allowed to be less than 0 or greater than 200
            - Give me an angle between 0 and 360 to show which way the road is starting. (0 = along the y axis).  the value has to be an integer
            - make sure that no point is out of bounds / every x and y value is greater than 0 and less than 200
            - the z axis can't be lower than -28.0
            - every segment needs the distance of the end point of the segment to the end point of the previous segment in meters, direction (e.g. right turn), the incline in % and the degrees of the turn!
            - Only return 'left', 'right' or 'straight' for the direction
            - Only return numbers for the distance, incline and the degrees of the turn.
            - Write declines in height and the degrees of right turns as negative numbers!
            - The maximum incline is 15%
            - The turn degrees of one segment should not exceed 70 degrees. If you want to create a turn with more degrees split it into two segments!
            - Return the road description in json format of {'starting_point': (x, y, z), 'theta': theta, 'road_segment1': {'distance': int, 'direction': str, 'incline': int, 'turn_degrees': int}, 'road_segment2': {'distance': int, 'direction': str, 'incline': int, 'turn_degrees': int}}, etc.
            - Given the same prompt you should never return the same road description and your descriptions should be as diverse as possible (don't start with the same theta every time, don't start with a right turn every time, don't start at the same point, etc.)
            - Make the roads as diverse as possible (longer turns, shorter turns, incline, decline, etc.)
            - Keep track of where you are going since you are not allowed to go outside of the map boundaries!
            - The response has to be in json format!""",
            model = "gpt-3.5-turbo"
            
        )
        set_key(".env", "ROADGPT_ID", self.assistant_id)

        return roadgpt.id
    
    
    def create_thread(self):
        thread = self.client.beta.threads.create()
        self.threads.append(thread.id)

        return thread.id
    

    def create_run(self, thread_id):
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
    

class RoadGPT:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def prompt(self, prompt):
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages = [
                {
                    "role": "system",
                    "content": "You are a road designer, who designs roads to test the lane keeping functionality of self driving vehicles. People give you descriptions of roads and you create more detailed descriptions of novel roads, where you split the road into segments. These descriptions are then turned into coordinates, so keep the coordinate values in mind. Since you are testing the lane keeping functionality of self driving vehicles, you want to stress it. Here are some ground rules: - The roads should be diverse, that means given the same description don't create the same road (Start in different directions, etc.) - The car should cover as many directions on the map as possible / The car should face as many directions as possible while using your road. - before the first segment give me a starting point (x, y, z), consider your starting point when you build the road since the x and y values are not allowed to be less than 0 or greater than 200 - Give me an angle between 0 and 360 to show which way the road is starting. (0 = along the y axis).  the value has to be an integer - make sure that no point is out of bounds / every x and y value is greater than 0 and less than 200 - the z axis can't be lower than -28.0 - every segment needs the distance of the end point of the segment to the end point of the previous segment in meters, direction (e.g. right turn), the incline in % and the degrees of the turn! - Only return 'left', 'right' or 'straight' for the direction - Only return numbers for the distance, incline and the degrees of the turn. - Write declines in height and the degrees of right turns as negative numbers! - The maximum incline is 15% - The turn degrees of one segment should not exceed 70 degrees. If you want to create a turn with more degrees split it into two segments! - Return the road description in json format of {'starting_point': (x, y, z), 'theta': theta, 'road_segment1': {'distance': int, 'direction': str, 'incline': int, 'turn_degrees': int}, 'road_segment2': {'distance': int, 'direction': str, 'incline': int, 'turn_degrees': int}}, etc. - Given the same prompt you should never return the same road description and your descriptions should be as diverse as possible (don't start with the same theta every time, don't start with a right turn every time, don't start at the same point, etc.) - Make the roads as diverse as possible (longer turns, shorter turns, incline, decline, etc.) - Keep track of where you are going since you are not allowed to go outside of the map boundaries!"
                },
                {
                    "role": "user",
                    "content": prompt
                }],
            response_format={"type": "json_object"}
        )
        print(response.usage)
        return response.choices[0].message.content
    


if __name__ == "__main__":
    roadgpt = RoadGPTAssistant()
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