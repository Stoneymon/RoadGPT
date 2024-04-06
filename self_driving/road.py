import json
import uuid
import numpy as np
from typing import Tuple, List

class Road:
    def __init__(self, name, persistentID=None):
        self.name = name
        self.persistendID = persistentID if persistentID else str(uuid.uuid4())
        self.nodes = []

    def add_4d_points(self, nodes: List[Tuple[float, float, float, float]]):
        self.nodes += [list(item) for item in nodes]
        return self

    def to_dict(self):
        return {
            "name": self.name,
            "nodes": self.nodes
        }

    @classmethod
    def from_dict(cls, d):
        return Road(name=d["name"]).add_4d_points(nodes=d["nodes"])


class MeshRoad(Road):

    def __init__(self, name, persistentID=None):
        super().__init__(name, persistentID)
        self.material = "track_editor_A_center"

    def noise(self):
        return np.random.uniform(low=-0.001, high=0.001)

    def to_json(self):
        roadobj = {}
        roadobj["name"] = self.name
        roadobj["class"] = "MeshRoad"
        roadobj["breakAngle"] = 180
        roadobj["topMaterial"] = self.material
        roadobj["bottomMaterial"] = self.material
        roadobj["sideMaterial"] = self.material
        roadobj["widthSubdivisions"] = 0
        roadobj["rotationEuler"] = [0, 0, 0]
        roadobj["rotationMatrix"] = [1,0,0,0,1,0,0,0,1]
        roadobj["persistentID"] = self.persistendID
        roadobj["__parent"] = "generated"
        roadobj["position"] = tuple(self.nodes[0][:3])
        roadobj["textureLength"] = 5
        roadobj["nodes"] = [[item[0]+self.noise(), item[1]+self.noise(), item[2], 10, 5, 0, 0, 1] for item in self.nodes]
        return json.dumps(roadobj)


class DecalRoad(Road):

    def __init__(self, name, persistentID=None, drivability=1):
        super().__init__(name, persistentID)
        self.material = "tig_road_rubber_sticky"
        self.drivability = drivability

    def to_json(self):
        roadobj = {}
        roadobj['name'] = self.name
        roadobj['class'] = 'DecalRoad'
        roadobj['breakAngle'] = 180
        roadobj['distanceFade'] = [1000, 1000]
        roadobj['drivability'] = self.drivability
        roadobj['material'] = self.material
        roadobj['overObjects'] = True
        roadobj['persistentId'] = self.persistentId
        roadobj['__parent'] = 'generated'
        roadobj['position'] = tuple(self.nodes[0][:3])  # keep x,y,z discard width
        roadobj['textureLength'] = 2.5
        roadobj['nodes'] = [(item[0], item[1], item[2], 8) for item in self.nodes]
        return json.dumps(roadobj)