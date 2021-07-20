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

from RhombusAPI.models.hardware_variation_enum import HardwareVariationEnum
from logging_utils.colors import LogColors

class RhombusCameraSpecs:
    """Holds data about Rhombus Cameras

    :attribute FOV: The field of view of the camera.
    :attribtue view_distance: The view distance of humans in meters of the camera.
    """

    FOV: float
    view_distance: float

    def __init__(self, FOV: float, view_distance: float):
        """Constructor for the Main class, which will initialize all of the clients and arguments

        :param FOV: The field of view of the camera.
        :param view_distance: The view distance of humans in meters of the camera.
        """

        self.FOV = FOV
        self.view_distance = view_distance


def get_camera_specs(camera_hardware: HardwareVariationEnum) -> RhombusCameraSpecs:
    """Gets the camera FOV for a specific model

    :param camera_hardware: The camera hardware model
    :return: Returns the hardware specs of the camera
    """

    if camera_hardware == HardwareVariationEnum.CAMERA_R100:
        return RhombusCameraSpecs(96, 57) 
    elif camera_hardware == HardwareVariationEnum.CAMERA_R1:
        return RhombusCameraSpecs(135, 44)
    elif camera_hardware == HardwareVariationEnum.CAMERA_R2:
        return RhombusCameraSpecs(96,57)
    elif camera_hardware == HardwareVariationEnum.CAMERA_R200:
        return RhombusCameraSpecs(112, 57)
    else:
        print(LogColors.WARNING + "Running unsupported camera!" + camera_hardware.to_str() + " Using default FOV and view distance settings!" + LogColors.ENDC)
        return RhombusCameraSpecs(112, 57)
