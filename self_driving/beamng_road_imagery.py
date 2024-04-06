import matplotlib.pyplot as plt

from self_driving.road_points import RoadPoints


class BeamNGRoadImagery:
    def __init__(self, road_points: RoadPoints):
        self.road_points = road_points
        self._fig, self._ax = None, None
        self._heightfig, self._heightax = None, None

    def plot(self):
        self._close()
        self._fig, self._ax = plt.subplots(1)
        self.road_points.plot_on_ax(self._ax)
        self._ax.axis('equal')
        self.plot_height()

    def plot_height(self):
        self._heightfig, self._heightax = plt.subplots(1)
        self.road_points.plot_height_on_ax(self._heightax)
        #self._heightax.axis('tight')

    def save(self, image_path):
        if not self._fig:
            self.plot()
        self._fig.savefig(image_path)

    def save_height_fig(self, image_path):
        if not self._heightfig:
            self.plot()
        self._heightfig.savefig(image_path)

    @classmethod
    def from_sample_nodes(cls, sample_nodes):
        return BeamNGRoadImagery(RoadPoints().add_middle_nodes(sample_nodes))

    def _close(self):
        if self._fig:
            plt.close(self._fig)
            self._fig = None
            self._ax = None
            self._heightfig = None
            self._heightax = None

    def __del__(self):
        self._close()