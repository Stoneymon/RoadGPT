import matplotlib.pyplot as plt

from self_driving.road_points import RoadPoints


class BeamNGRoadImagery:
    def __init__(self, road_points: RoadPoints):
        self.road_points = road_points
        self._fig, self._ax = None, None
        self._heightfig, self._heightax = None, None

    def move_plot(self):
        x_vals = [road_point[0] for road_point in self.road_points.middle]
        y_vals = [road_point[1] for road_point in self.road_points.middle]
        # min_x = min(x_vals) - 4
        # min_y = min(y_vals) - 4

        centroid_x = sum(x_vals) / len(x_vals)
        centroid_y = sum(y_vals) / len(y_vals)

        displacement_x = 80 - centroid_x
        displacement_y = 110 - centroid_y

        print(self.road_points.left[0])
        print(self.road_points.middle[0])
        print(self.road_points.right[0])

        for i in range(len(x_vals)):
            left_x = self.road_points.left[i][0] + displacement_x
            left_y = self.road_points.left[i][1] + displacement_y

            self.road_points.left[i] = (left_x, left_y)

            self.road_points.middle[i][0] = self.road_points.middle[i][0] + displacement_x
            self.road_points.middle[i][1] = self.road_points.middle[i][1] + displacement_y

            right_x = self.road_points.right[i][0] + displacement_x
            right_y = self.road_points.right[i][1] + displacement_y

            self.road_points.right[i] = (right_x, right_y)

            # left_x = self.road_points.left[i][0] - min_x
            # left_y = self.road_points.left[i][1] - min_y

            # self.road_points.left[i] = (left_x, left_y)

            # self.road_points.middle[i][0] = self.road_points.middle[i][0] - min_x
            # self.road_points.middle[i][1] = self.road_points.middle[i][1] - min_y

            # right_x = self.road_points.right[i][0] - min_x
            # right_y = self.road_points.right[i][1] - min_y

            # self.road_points.right[i] = (right_x, right_y)

        # print(self.road_points.middle)
        # print(x_vals)
        # print(y_vals)

    def plot(self):
        self._close()
        self._fig, self._ax = plt.subplots(1)
        # self.move_plot()
        self.road_points.plot_on_ax(self._ax)
        # self._ax.axis('tight')
        self._ax.set_title("Top down view")
        self._ax.set_xlabel("x-coordinate (1 unit = 1 meter)")
        self._ax.set_ylabel("y-coordinate (1 unit = 1 meter)")
        self._ax.set_xlim(0, 220)
        self._ax.set_ylim(0, 220)
        self.plot_height()

    def plot_height(self):
        self._heightfig, self._heightax = plt.subplots(1)
        self.road_points.plot_height_on_ax(self._heightax)
        self._heightax.set_title("Distance vs altitude")
        self._heightax.set_xlabel("Distance from the starting point in m")
        self._heightax.set_ylabel("Altitude in m")
        self._heightax.set_xlim(0, 200)
        self._heightax.set_ylim(-20, 20)
        #self._heightax.axis('tight')

    def save(self, image_path):
        if not self._fig:
            self.plot()
        self._fig.savefig(image_path)

    def save_height_fig(self, image_path):
        if not self._heightfig:
            self.plot(height=True)
        self._heightfig.savefig(image_path)

    @classmethod
    def from_sample_nodes(cls, sample_nodes):
        return BeamNGRoadImagery(RoadPoints().add_middle_nodes(sample_nodes))

    def _close(self):
        if self._fig:
            plt.close(self._fig)
            plt.close(self._heightfig)
            self._fig = None
            self._ax = None
            self._heightfig = None
            self._heightax = None

    def __del__(self):
        self._close()