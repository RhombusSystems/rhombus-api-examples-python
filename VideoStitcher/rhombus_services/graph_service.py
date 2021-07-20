###################################################################################
# Copyright (c) 2021 Rhombus Systems                                              #
#                                                                                 # 
# Permission is hereby granted, free of charge, to any person obtaining a copy    #
# of this software and associated documentation files (the "Software"), to deal   #
# in the Software without restriction, including without limitation the rights    #
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell       #
# copies of the Software, and to permit persons to whom the Software is           #
# furnished to do so, subject to the following conditions:                        #
#                                                                                 # 
# The above copyright notice and this permission notice shall be included in all  #
# copies or substantial portions of the Software.                                 #
#                                                                                 # 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR      #
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,        #
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE     #
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER          #
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,   #
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE   #
# SOFTWARE.                                                                       #
###################################################################################

from typing import List
import numpy as np
import math 

from rhombus_types.camera import Camera
from rhombus_types.vector import Vec2

from rhombus_utils.utils import geodetic_to_enu_simple_approximation
from rhombus_types.matrix import rotate
from rhombus_utils.math import normalize_angle

class CameraPlot:
    """The plot of a camera containing its vertices and other relevant information

    :attribute x: The array of x coordinates for the camera vertices
    :attribute y: The array of y coordinates for the camera vertices
    :attribute position: The position of the camera in meters from the origin camera
    :attribute rotation: The rotation of the camera in radians using our own coordinate space, where 0 is East and PI / 2 is North
    :attribute uuid: The UUID of the camera
    """

    x: List[float]
    y: List[float]
    position: np.ndarray
    rotation: float
    uuid: str

    def __init__(self, x: List[float], y: List[float], position: np.ndarray, rotation: float, uuid: str):
        """Constructor for the Main class, which will initialize all of the clients and arguments

        :param x: The array of x coordinates for the camera vertices
        :param y: The array of y coordinates for the camera vertices
        :param position: The position of the camera in meters from the origin camera
        :param rotation: The rotation of the camera in radians using our own coordinate space, where 0 is East and PI / 2 is North
        :param uuid: The UUID of the camera
        """

        self.x = x
        self.y = y
        self.position = position
        self.rotation = rotation
        self.uuid = uuid


def get_camera_side_radius(angle: float, camera_distance: float) -> float:
    """Gets the length of the sides of the triangle FOV when rendering the triangle vertices

    :param angle: The angle of the camera in radians in our own coordinate space, where 0 is East and PI / 2 is North
    :param camera_distance: The distance that the camera can see on average in meters (this is not an exact measurement, this is just a general statement about how far the camera can see)
    :return: Returns the length of the side of the triangle FOV
    """

    return camera_distance / math.cos(angle)

def get_camera_plot(camera: Camera, origin: Camera):
    """Gets a camera plot for a specific camera

    :param camera: The camera to get the camera plot for
    :param origin: The origin camera which will be drawn at the center. This is necessary because all other camera's positions 
    will be based on this camera and will be rotated so that the origin camera will be rotated upward.

    :return: Returns the resulting camera plot of this camera
    """

    # Get the rotation of the camera in radians
    rot = camera.rotation_radians

    # Get the FOV fo the camera 
    fov = camera.FOV

    # Get the side radius using our FOV and viewDistance so taht we can draw a triangle
    camera_side_radius = get_camera_side_radius(fov / 2, camera.view_distance)

    # Get the offset of the camera from the origin in meters
    offset = geodetic_to_enu_simple_approximation(camera.location, origin.location)


	# This is how we want to render our triangle of the camera in local space
	# ###########
	#  ########
	#   ###### 
	#    ####  
	#     ##  


    #  Get the X and Y positions of the camera vertices.    
    positions: List[np.ndarray] = [
                # The starting vertex in the local space will be the top left of the triangle. (refer to the image above)
                Vec2(
                    camera_side_radius * math.cos(rot + fov / 2) + offset[0],
                    camera_side_radius * math.sin(rot + fov / 2) + offset[1],
                    ),
                # The second vertex in the local space will be bottom middle of the triangle. (refer to the image above)
                Vec2(
                    offset[0],
                    offset[1],
                    ),
                # The final vertex in the local space will be the top right of the triangle. (refer to the image above).
                Vec2(
                    camera_side_radius * math.cos(rot - fov / 2) + offset[0],
                    camera_side_radius * math.sin(rot - fov / 2) + offset[1],
                    ),

            ]

    # We need to rotate the triangle above so that it lines up with the camera in the origin, which will be in the center and facing up.
    # The first step is to get the offset rotation in radians
    offset_rotation = normalize_angle(math.pi / 2 - origin.rotation_radians)

    # Then we will create a 2x2 rotation matrix from this offset rotation so we can rotate all of our vertices
    rotation = rotate(offset_rotation)

    # Then we will rotate all of our vertices by that rotation matrix
    positions = list(map(lambda pos: rotation.dot(pos), positions))

    # Then return thee result as a camera plot
    return CameraPlot(
                    x=list(map(lambda pos: pos[0], positions)),
                    y=list(map(lambda pos: pos[1], positions)),
                    uuid=camera.uuid,

                    # We will add our offsetRotation so that the rotation of the camera is in world space
                    rotation=offset_rotation + rot,
                    position=positions[1]
            )
