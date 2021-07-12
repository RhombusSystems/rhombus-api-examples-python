from typing import List
from rhombus_types.camera import Camera
from rhombus_types.vector import Vec2
from rhombus_utils.math import degrees_to_radians, convert_rhombus_angle
from rhombus_utils.utils import feet_to_meters
from rhombus_utils.rhombus_camera_info import get_camera_specs

import RhombusAPI as rapi

def get_camera_list(api_client: rapi.ApiClient) -> List[Camera]:
    """Gets the list of Rhombus Systems Cameras

    :param api_client: The API Client for sending requests to Rhombus
    :return: Returns the list of cameras
    """

    # Create the api
    cam_api = rapi.CameraWebserviceApi(api_client = api_client)

    get_minimal_state_list_request = rapi.CameraGetMinimalCameraStateListWSRequest()
    res = cam_api.get_minimal_camera_state_list(body=get_minimal_state_list_request)

    res.camera_states = filter(lambda element: element.latitude is not None and element.longitude is not None and element.direction_radians is not None, res.camera_states) 

    return list(
            map(lambda camera: 
                Camera(uuid=camera.uuid,
                    rotation_radians=convert_rhombus_angle(camera.direction_radians),
                    location=Vec2(camera.latitude, camera.longitude),
                    FOV=degrees_to_radians(get_camera_specs(camera.hw_variation).FOV),
                    view_distance=feet_to_meters(get_camera_specs(camera.hw_variation).view_distance)
                ),
                res.camera_states,
            )
    )

