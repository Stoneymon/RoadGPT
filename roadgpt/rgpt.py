from dotenv import load_dotenv, set_key
from openai import OpenAI
import os
import time

load_dotenv(os.path.join(os.getcwd(), '..', '.env'))

class RGPT:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def prompt(self, prompt):
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages = [
                {
                    "role": "system", 
                    "content": """
You are a road designer, who designs roads to test the lane keeping functionality of self driving vehicles. People give you descriptions of roads and you create more detailed descriptions of novel roads, where you split the road into segments. These descriptions are then turned into coordinates, so keep the coordinate values in mind. Since you are testing the lane keeping functionality of self driving vehicles, you want to stress it.

Here are some ground rules:
- The roads should be diverse, that means given the same description don't create the same road (Start in different directions, etc.)
- The car should cover as many directions on the map as possible / The car should face as many directions as possible while using your road.
- before the first segment give me a starting point (x, y, z), consider your starting point when you build the road since the x and y values are not allowed to be less than 0 or greater than 200
- Give me an angle between 0 and 360 to show which way the road is starting. (0 = along the y axis).  the value has to be an integer
- make sure that no point is out of bounds / every x and y value is greater than 0 and less than 200
- the z axis can't be lower than -28.0
- Each turn / straight is it's own segment.
- Every change in incline is it's own segment.
- For every segment return the distance of the end point of the segment to the end point of the previous segment in meters, direction (e.g. right turn), the incline in % and the degrees of the turn in case it is a turn.
- Only return "left", "right" or "straight" for the direction
- Only return numbers for the distance, incline and the degrees of the turn.
- Write declines in height and the degrees of left turns as negative numbers.
- The maximum incline is 15%
- The turns should not exceed 89 degrees, if you want to create turns between 90 and 180 degrees create two segments facing the same direction right after each other with turn degrees < 90 degrees each
- Return the road description in json format of {'starting_point': (x, y, z), 'theta': theta, 'road_segment1': {'distance': int, 'direction': str, 'incline': int, 'turn_degrees': int}, 'road_segment2': {'distance': int, 'direction': str, 'incline': int, 'turn_degrees': int}}, etc.
- Given the same prompt you should never return the same road description and your descriptions should be as diverse as possible (don't start with the same theta every time, don't start with a right turn every time, don't start at the same point, etc.)
- Remember that you can never cross or touch the map boundaries of 0 and 200 on each axis.
- Make the roads as diverse as possible (longer turns, shorter turns, incline, decline, etc.)
- Create the roads with at least 7 and at most 15 segments
- The response has to be in json format!"""
                },
                {
                    "role": "user", 
                    "content": prompt}
                    ]
            # response_format={ "type": "json_object" }
        )
        return response

if __name__=="__main__":
    rgpt = RGPT()
    response = rgpt.prompt("Create a mountain road with serpentines.")
    print(response.choices[0].message.content)