import logging as log

from beamngpy import BeamNGpy, Scenario, Vehicle
from road import MeshRoad, DecalRoad
from beamng_pose import BeamNGPose

class BeamNGBrewer:
    def __init__(self, beamng_home=None, beamng_user=None, road_nodes=None):
        self.scenario = None

        self.beamng = BeamNGpy("localhost", 64256, home=beamng_home, user=beamng_user)
        self.beamng.open(launch=True)

        self.vehicle = None
        if road_nodes:
            self.setup_road(road_nodes)

        self.vehicle_start_pose = BeamNGPose()

    def setup_road(self, road_nodes):
        self.road_nodes = road_nodes
        self.mesh_road = MeshRoad('mesh_1')
        self.decal_road = DecalRoad('street_1')

    def setup_vehicle(self):
        self.vehicle = Vehicle("ego_vehicle", model="etk800", licence="RGPT", color="black")
        return self.vehicle

    def bring_up(self):
        self.scenario = Scenario("tig", "tigscenario")
        if self.vehicle:
            self.scenario.add_vehicle(self.vehicle, pos=self.vehicle_start_pose.pos, rot_quat=self.vehicle_start_pose.rot)

        self.scenario.make(self.beamng)
        self.beamng.set_deterministic()
        self.beamng.load_scenario(self.scenario)

        self.beamng.start_scenario()

        self.beamng.pause()