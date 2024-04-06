#
# This file contains the code originally developed for DeepHyperion for computing exemplary test features.
# Please refer to the following paper and github repo:
# 	Tahereh Zohdinasab, Vincenzo Riccio, Alessio Gambi, Paolo Tonella:
#   DeepHyperion: exploring the feature space of deep learning-based systems through illumination search.
#   ISSTA 2021: 79-90
#
#   Repo URL: https://github.com/testingautomated-usi/DeepHyperion
#

import logging as logger
import math

import numpy as np

from shapely.geometry import Point
from code_pipeline.utils import pairwise

THE_NORTH = [0, 1]


####################################################################################
# Private Utility Methods
####################################################################################


def _calc_angle_distance(v0, v1):
    at_0 = np.arctan2(v0[1], v0[0])
    at_1 = np.arctan2(v1[1], v1[0])
    return at_1 - at_0


def _calc_dist_angle(points):
    assert len(points) >= 2, f'at least two points are needed'

    def vector(idx):
        return np.subtract(points[idx + 1], points[idx])

    n = len(points) - 1
    result = [None] * (n)
    b = vector(0)
    for i in range(n):
        a = b
        b = vector(i)
        angle = _calc_angle_distance(a, b)
        distance = np.linalg.norm(b)
        result[i] = (angle, distance, [points[i + 1], points[i]])
    return result


# TODO Possibly code duplicate
def _define_circle(p1, p2, p3):
    """
    Returns the center and radius of the circle passing the given 3 points.
    In case the 3 points form a line, returns (None, infinity).
    """
    temp = p2[0] * p2[0] + p2[1] * p2[1]
    bc = (p1[0] * p1[0] + p1[1] * p1[1] - temp) / 2
    cd = (temp - p3[0] * p3[0] - p3[1] * p3[1]) / 2
    det = (p1[0] - p2[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p2[1])

    if abs(det) < 1.0e-6:
        return None, np.inf

    # Center of circle
    cx = (bc * (p2[1] - p3[1]) - cd * (p1[1] - p2[1])) / det
    cy = ((p1[0] - p2[0]) * cd - (p2[0] - p3[0]) * bc) / det
    center = Point(cx, cy)

    radius = np.sqrt((cx - p1[0]) ** 2 + (cy - p1[1]) ** 2)
    return center, radius


####################################################################################
# Structural Features
####################################################################################

# Measure the coverage of road directions w.r.t. to the North (0,1) using the control points of the given road
# to approximate the road direction. By default we use 36 bins to have bins of 10 deg each
def get_thetas(xs, ys, skip=1):
    """Transform x,y coordinates of points and return each segment's offset from x-axis in the range [np.pi, np.pi]"""
    xdiffs = xs[1:] - xs[0:-1]
    ydiffs = ys[1:] - ys[0:-1]
    thetas = np.arctan2(ydiffs, xdiffs)
    return thetas


# Fixed direction coverage as suggested in Issue #114 by stklk
def direction_coverage_klk(the_test, n_bins=36):
    if not isinstance(the_test, list):
        the_test = the_test.interpolated_points
    np_arr = np.array(the_test)
    thetas = get_thetas(np_arr[:, 0], np_arr[:, 1])
    coverage_buckets = np.linspace(-np.pi, np.pi, num=n_bins)
    covered_elements = set(np.digitize(thetas, coverage_buckets))
    dir_coverage = len(covered_elements) / len(coverage_buckets)
    return "DIR_COV", dir_coverage


# Measure the coverage of road directions w.r.t. to the North (0,1) using the control points of the given road
# to approximate the road direction. By default we use 36 bins to have bins of 10 deg each
def direction_coverage(the_test, n_bins=25):
    coverage_buckets = np.linspace(0.0, 360.0, num=n_bins + 1)
    direction_list = []
    if not isinstance(the_test, list):
        the_test = the_test.interpolated_points

    for a, b in pairwise(the_test):
        # Compute the direction of the segment defined by the two points
        road_direction = [b[0] - a[0], b[1] - a[1]]
        # Compute the angle between THE_NORTH and the road_direction.
        # E.g. see: https://www.quora.com/What-is-the-angle-between-the-vector-A-2i+3j-and-y-axis
        # https://www.kite.com/python/answers/how-to-get-the-angle-between-two-vectors-in-python
        unit_vector_1 = road_direction / np.linalg.norm(road_direction)
        dot_product = np.dot(unit_vector_1, THE_NORTH)
        angle = math.degrees(np.arccos(dot_product))
        direction_list.append(angle)

    # Place observations in bins and get the covered bins without repetition
    covered_elements = set(np.digitize(direction_list, coverage_buckets))
    dir_coverage = len(covered_elements) / len(coverage_buckets)
    return "DIR_COV", dir_coverage


def max_curvature(the_test, w=5):
    if not isinstance(the_test, list):
        nodes = the_test.interpolated_points
    else:
        nodes = the_test
    min_radius = np.inf
    for i in range(len(nodes) - w):
        p1 = nodes[i]
        p2 = nodes[i + int((w - 1) / 2)]
        p3 = nodes[i + (w - 1)]

        # We care only about the radius of the circle here
        _, radius = _define_circle(p1, p2, p3)
        if radius < min_radius:
            min_radius = radius
    # Max curvature is the inverse of Min radius
    curvature = 1.0 / min_radius

    return "MAX_CURV", curvature

def  max_diff_altitude(the_test):
    if not isinstance(the_test, list):
        nodes = the_test.interpolated_points
    else:
        nodes = the_test
    z_vals = [node[2] for node in nodes]
    highest = max(z_vals)
    lowest = min(z_vals)
    return "MAX_DIFF_ALT", highest - lowest

def get_distances(nodes):
    """
    returns the distances and z_values for calculating the gradients
    x = distances to origin
    y = z_values
    """
    x = [0]
    for i in range(1, len(nodes)):
        x.append(x[-1] + (np.sqrt((nodes[i][0] - nodes[i-1][0]) ** 2 + (nodes[i][1] - nodes[i-1][1]) ** 2)))
    y = [node[2] for node in nodes]
    return x, y

def rolling_window(nodes, step=10):
    """
    returns the rolling window of the nodes (default window size = 10)
    """
    return [nodes[pos:pos + step] for pos in range(0, len(nodes), step)]


def get_rw_gradients(the_test):
    """
    returns the avg of a rolling window of gradients
    """
    if not isinstance(the_test, list):
        nodes = the_test.interpolated_points
    else:
        nodes = the_test
    x, y = get_distances(nodes)
    gradients = list(np.gradient(y, x))
    grouped_gradients = rolling_window(gradients)
    avg_gradients = [np.mean(group) for group in grouped_gradients]
    return avg_gradients

def max_slope(the_test):
    avg_gradients = get_rw_gradients(the_test)
    return "MAX_SLOPE", max(avg_gradients)

def min_slope(the_test):
    avg_gradients = get_rw_gradients(the_test)
    return "MIN_SLOPE", min(avg_gradients)

def sd_slope(the_test):
    avg_gradients = get_rw_gradients(the_test)
    return "STD_SLOPE", np.std(avg_gradients)

def segment_count(the_test):
    avg_gradients = get_rw_gradients(the_test)
    direction = None
    up_segment_count = 0
    down_segment_count = 0
    flat_segment_count = 0
    cons_flat_segments = 0

    for i in range(1, len(avg_gradients)):
        if avg_gradients[i] > 0.02:
            if direction != "up":
                up_segment_count += 1
                direction = "up"
        elif avg_gradients[i] < -0.02:
            if direction != "down":
                down_segment_count += 1
                direction = "down"
        else:
            if direction != "flat":
                direction = "flat"
                cons_flat_segments += 1
            elif cons_flat_segments == 1:
                flat_segment_count += 1
                cons_flat_segments = 0

    return "NR_OF_SEGMENTS", {"upwards": up_segment_count, "downwards": down_segment_count, "horizontal": flat_segment_count}


#
# def plateaus(the_test):
#     if not isinstance(the_test, list):
#         nodes = the_test.interpolated_points
#     else:
#         nodes = the_test
#     x = [0]
#     for i in range(1, len(nodes)):
#         x.append(x[-1] + (np.sqrt((nodes[i][0] - nodes[i-1][0]) ** 2 + (nodes[i][1] - nodes[i-1][1]) ** 2)))
#     y = [node[2] - nodes[0][2] for node in nodes]
#     gradients = list(np.gradient(y, x))
#     start = 0
#     end = 1
#     added = False
#     plateaus = []
#     for i in range(len(gradients)):
#         if abs(gradients[i]) <= 0.1:
#             if start < end:
#                 start = i
#                 added = False
#             elif start > end:
#                 end = i
#         elif not added and start != end:
#             plateaus.append([nodes[start], nodes[end]])
#             added = True
#     # plateau_indices = [gradients.index(i) for i in gradients if abs(i) <= 0.1]
#     return "PLATEAUS", plateaus
#
# def smoothness(the_test):
#     if not isinstance(the_test, list):
#         nodes = the_test.interpolated_points
#     else:
#         nodes = the_test
#     z_vals = np.array([node[2] for node in nodes])
#     algo = rpt.Pelt(model="l2").fit(z_vals)
#     result = algo.predict(pen=5)
#
#     result = len(result)
#
#     return "CHANGEPOINTS", result


####################################################################################
# Behavioural Features
####################################################################################


#  Standard Deviation of Steering Angle accounts for the variability of the steering
#   angle during the execution
def sd_steering(execution_data):
    steering = []
    for state in execution_data:
        steering.append(state.steering)
    sd_steering = np.std(steering)
    return "STD_SA", sd_steering


#  Mean of Lateral Position of the car accounts for the average behavior of the car, i.e.,
#   whether it spent most of the time traveling in the center or on the side of the lane
def mean_lateral_position(execution_data):
    lp = []
    for state in execution_data:
        lp.append(state.oob_distance)

    mean_lp = np.mean(lp)
    return "MEAN_LP", mean_lp


def max_lateral_position(execution_data):
    lp = []
    for state in execution_data:
        lp.append(state.oob_distance)

    max_lp = np.max(lp)
    return "MAX_LP", max_lp

def sd_throttle(execution_data):
    throttle = []
    for state in execution_data:
        throttle.append(state.throttle)
    sd_throttle = np.std(throttle)
    return "STD_THROTTLE", sd_throttle

def sd_brake(execution_data):
    brake = []
    for state in execution_data:
        brake.append(state.brake)
    sd_brake = np.std(brake)
    return "STD_BRAKE", sd_brake

def get_gforces(execution_data):
    gforces_x = []
    gforces_y = []
    gforces_z = []
    for state in execution_data:
        gforces_x.append(abs(state.gforce_x)/9.81)
        gforces_y.append(abs(state.gforce_y)/9.81)
        gforces_z.append(abs(state.gforce_z)/9.81)
    return gforces_x, gforces_y, gforces_z

def mean_gforces(execution_data):
    gforces_x, gforces_y, gforces_z = get_gforces(execution_data)
    gforces = {'x': np.mean(gforces_x), 'y': np.mean(gforces_y), 'z': np.mean(gforces_z)}
    return "MEAN_GFORCES", gforces

def sd_gforces(execution_data):
    gforces_x, gforces_y, gforces_z = get_gforces(execution_data)
    gforces = {'x': np.std(gforces_x), 'y': np.std(gforces_y), 'z': np.std(gforces_z)}
    return "STD_GFORCES", gforces

def max_gforces(execution_data):
    gforces_x, gforces_y, gforces_z = get_gforces(execution_data)
    gforces = {'x': max(gforces_x), 'y': max(gforces_y), 'z': max(gforces_z)}
    return "MAX_GFORES", gforces



def compute_all_features(the_test, execution_data):
    # TODO think about implementation of 3D features (smoothness, gradient, plateau, banking, occlusion)
    # TODO landscape analysis https://pylandstats.readthedocs.io/en/latest/landscape.html
    features = dict()
    # Structural Features
    structural_features = [max_curvature, direction_coverage, max_diff_altitude, max_slope, min_slope, sd_slope, segment_count]

    # TODO: changepoint analysis: https://github.com/deepcharles/ruptures


    # Behavioural Features
    behavioural_features = [sd_steering, mean_lateral_position, max_lateral_position, sd_throttle, sd_brake, mean_gforces,
                            sd_gforces, max_gforces]

    logger.debug("Computing structural features")
    for h in structural_features:
        key, value = h(the_test)
        features[key] = value

    # TODO Add minimum value here
    if len(execution_data) > 2:
        logger.debug("Computing output features")
        for h in behavioural_features:
            key, value = h(execution_data)
            features[key] = value

    return features