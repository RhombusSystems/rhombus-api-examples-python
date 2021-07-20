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
