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
from rhombus_services.graph_service import get_camera_plot

def get_canvas_size(cameras: List[Camera], origin_camera: Camera) -> np.ndarray:
    """Gets the size in meters of a canvas for a list of cameras. This method basically gives the smallest box in meters that encloses all of the cameras and their FOVs.

    :param cameras: The list of cameras to put a box around.
    :param origin_camera: The camera that should be at the center of the box and facing up. This method will get a camera plot and then based on that plot put a box around all of them.
    :return: Returns the dimensions in meters of the box.
    """

    # We are going to store 2 values, the maximum distance X and the maximum distance Y from the `originCamera`
    extreme_x: float = 0
    extreme_y: float = 0

    # Loop through all of the cameras
    for camera in cameras: 
        # If there is no rotation (if it's not on the map) then we can't do anything
        if math.isnan(camera.rotation_radians):
            continue

        # Get the camera plot so we know where all of the "vertices" of the camera are
        plot = get_camera_plot(camera, origin_camera)

        # Loop through all of the x values of the vertices
        for x in plot.x:
            
            # If the absolute value of X is greater than the `extremeX`, that means this x value should be the new extreme.
            # We are doing absolute value here because we do not care if this X value is positive or negative, just its distance from the originCamera which we consider as (0, 0)
            if abs(x) > abs(extreme_x):

                # Update the extreme value
                extreme_x = x

        # Loop through all of the y values of the vertices
        for y in plot.y:

            # If the absolute value of Y is greater than the `extremeY`, that means this y value should be the new extreme.
            # We are doing absolute value here because we do not care if this Y value is positive or negative, just its distance from the originCamera which we consider as (0, 0)
            if abs(y) > abs(extreme_y):

                # Update the extreme value
                extreme_y = y

    
    width = abs(extreme_x) * 2
    height = abs(extreme_y) * 2

    # We will just create a square with either both the width or both of the height values. We will figure out which one is greater and use that for our Vec2. 
    if width >= height:
        return Vec2(width, width)
    else:
        return Vec2(height, height)
