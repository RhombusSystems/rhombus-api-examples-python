import numpy as np
from rhombus_types.camera import Camera
from rhombus_types.vector import validate_vec2

class HumanEvent:
    """This is represents a single human bounding box at a specific timestamp. 

    :attribute id: The ObjectID of this human event.
    :attribute position: The position permyriad of the bounding box this human event is for
    :attribute dimensions: The size permyriad of the bounding box this human event is for
    :attribute timestamp: The timestamp in miliseconds at which this human event occurs
    :attribute camera: The camera for this human event
    """

    id: int
    position: np.ndarray
    dimensions: np.ndarray
    timestamp: int
    camera: Camera

    def __init__(self, id: int, position: np.ndarray, dimensions: np.ndarray, timestamp: int, camera: Camera):
        """Constructor for a Human Event

        :param id: The ObjectID of this human event.
        :param position: The position permyriad of the bounding box this human event is for
        :param dimensions: The size permyriad of the bounding box this human event is for
        :param timestamp: The timestamp in miliseconds at which this human event occurs
        :param camera: The camera for this human event
        """

        validate_vec2(position)
        validate_vec2(dimensions)

        self.id = id
        self.position = position
        self.dimensions = dimensions
        self.timestamp = timestamp
        self.camera = camera

