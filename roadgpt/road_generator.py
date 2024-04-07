import math
import numpy as np

from shapely.geometry import LineString
from scipy.interpolate import splev, splprep
from code_pipeline.tests_generation import RoadTestFactory

class RoadGenerator:
    def __init__(self, starting_point, segments):
        print("RoadGenerator init")
        self.starting_point = starting_point
        self.segments = segments
        self.nodes = [self.starting_point]
        self.theta = 0
        self.interpolated_nodes = None

    def translate_to_nodes(self):
        for segment in self.segments:
            if self.segments[segment]["direction"] == "left" and self.segments[segment]["turn_degrees"] > 0:
                self.theta -= self.segments[segment]["turn_degrees"]
            else:
                self.theta += self.segments[segment]["turn_degrees"]

            self.calculate_next_node(self.segments[segment]["distance"], self.segments[segment]["incline"])

    
    def deg_to_rad(self, degrees):
        print("RoadGenerator deg_to_rad")
        return degrees * math.pi / 180
    

    def calculate_incline(self, distance, incline):
        print("RoadGenerator calculate_incline")
        return distance * (incline / 100)
    
    
    def calculate_next_node(self, distance, incline):
        print("RoadGenerator calculate_next_node")
        angle_rad = self.deg_to_rad(self.theta)

        x_start, y_start, z_start = self.nodes[-1]

        x_end = x_start + distance * math.cos(angle_rad)
        y_end = y_start + distance * math.sin(angle_rad)
        z_end = z_start + self.calculate_incline(distance, incline)

        new_node = (x_end, y_end, z_end)

        self.nodes.append(new_node)

        return new_node
    

    def interpolate_road(self, road_nodes):
        """
            Interpolate the road points using cubic splines and ensure we handle 4F tuples for compatibility
        """
        print("RoadGenerator interpolate_road")
        interpolation_distance = 1
        min_num_nodes = 20
        rounding_precision = 3
        smoothness = 0

        old_x_vals = [n[0] for n in road_nodes]
        old_y_vals = [n[1] for n in road_nodes]
        old_z_vals = [n[2] for n in road_nodes]

        # This is an approximation based on whatever input is given
        test_road_length = LineString([(n[0], n[1], n[2]) for n in road_nodes]).length
        num_nodes = int(test_road_length / interpolation_distance)
        if num_nodes < min_num_nodes:
            num_nodes = min_num_nodes

        assert len(old_x_vals) >= 2, "You need at least two road points to define a road"
        assert len(old_y_vals) >= 2, "You need at least two road points to define a road"

        if len(old_x_vals) == 2:
            # With two points the only option is a straight segment
            k = 1
        elif len(old_x_vals) == 3:
            # With three points we use an arc, using linear interpolation will result in invalid road tests
            k = 2
        else:
            # Otheriwse, use cubic splines
            k = 3

        pos_tck, pos_u = splprep([old_x_vals, old_y_vals, old_z_vals], s=smoothness, k=k)

        step_size = 1 / num_nodes
        unew = np.arange(0, 1 + step_size, step_size)

        new_x_vals, new_y_vals, new_z_vals = splev(unew, pos_tck)

        self.interpolated_nodes = list(zip([round(v, rounding_precision) for v in new_x_vals],
                                           [round(v, rounding_precision) for v in new_y_vals],
                                           [v for v in new_z_vals],
                                           [8.0 for v in new_x_vals]))

        # Return the 4-tuple with default z and defatul road width
        return 
    
    def start(self, executor):
        self.executor = executor
        print(self.nodes)
        the_test = RoadTestFactory.create_road_test(self.nodes)
        print(the_test)
        # Send the test for execution
        test_outcome, description, execution_data = self.executor.execute_test(the_test)
        # Plot the OOB_Percentage: How much the car is outside the road?
        oob_percentage = [state.oob_percentage for state in execution_data]
        # log.info("Collected %d states information. Max is %.3f", len(oob_percentage), max(oob_percentage))

        # # Print test outcome
        # log.info("test_outcome %s", test_outcome)
        # log.info("description %s", description)

        import time
        time.sleep(10)
    

    def __repr__(self) -> str:
        return self.nodes
    
    def __str__(self):
        return str(self.nodes)