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

import numpy as np
from rhombus_types.vector import validate_vec2

class Camera:
    """This is represents a Rhombus Systems Camera

    :attribute uuid: The UUID of this camera
    :attribute rotation_radians: The rotation of this camera in radians.
                                 These are converted radians, NOT the direct radians given from rhombus. In this coordinate space, 0 is east, PI / 2 is north, and PI is west etc...
    :attribute location: The latitude (x) and longitude (y) location of this camera
    :attribute FOV: The field of view of this camera.
                    This changes depending on the Rhombus Camera type and is used in determining which cameras are located next to each other
    :attribute view_distance: The distance in meters on average this camera will see.
                              This obviously is not exact because this will change based on the up and down rotation of the camera,
                              but this is a good enough number that we can use to detect which cameras are near each other
    """

    uuid: str
    rotation_radians: float
    location: np.ndarray
    FOV: float
    view_distance: float

    def __init__(self, uuid: str, rotation_radians: float, location: np.ndarray, FOV: float, view_distance: float):
        """Constructor for a Camera

        :param uuid: The UUID of this camera
        :param rotation_radians: The rotation of this camera in radians.
                                 These are converted radians, NOT the direct radians given from rhombus. In this coordinate space, 0 is east, PI / 2 is north, and PI is west etc...
        :param location: The latitude (x) and longitude (y) location of this camera
        :param FOV: The field of view of this camera.
        :param view_distance: The distance in meters on average this camera will see.
        """
        validate_vec2(location)

        self.uuid = uuid
        self.rotation_radians = rotation_radians
        self.location = location
        self.FOV = FOV
        self.view_distance = view_distance


