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
