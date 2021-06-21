# Import type hints
from typing import List

# Import RhombusAPI to send requests to create our BoundingBoxes and seekpoints
import RhombusAPI as rapi


def rhombus_finalizer(api_client: rapi.ApiClient, camera_uuid: str,
                      bounding_boxes: List[rapi.FootageBoundingBoxType]) -> None:
    """Send all found bounding boxes to Rhombus to be created on the console

    :param api_client: The API Client to send requests
    :param camera_uuid: The UUID of the camera we want to create bounding boxes for
    :param bounding_boxes: The bounding boxes to add to the console
    """

    # If there were no created boxes, then we should return early
    if len(bounding_boxes) == 0:
        print("Detected no objects! Returning early...")
        return

    # Create the camera API with our client
    api = rapi.CameraWebserviceApi(api_client)

    # Send Rhombus our boundingBoxes, we actually don't have to do anything here since all the data has already been formatted properly
    response = api.create_footage_bounding_boxes(
        body=rapi.CameraCreateFootageBoundingBoxesWSRequest(camera_uuid=camera_uuid,
                                                            footage_bounding_boxes=bounding_boxes))

    # Debug info
    print("Rhombus responded with ")
    print(response)

    print("Creating footage seekpoints...")

    # We also are going to create some seekpoints, so we will create an empty array which will be filled according to our boundingBoxes data
    seekpoints: List[rapi.FootageSeekPointV2Type] = []

    # Add new seekpoints for all of our bounding boxes with the timestamp of those boxes
    for box in bounding_boxes:
        seekpoints.append(rapi.FootageSeekPointV2Type(a=rapi.ActivityEnum.CUSTOM, ts=box.ts, cdn=box.cdn))

    # Create all of our seekpoints
    response = api.create_footage_seekpoints(
        body=rapi.CameraCreateFootageSeekpointsWSRequest(camera_uuid=camera_uuid, footage_seek_points=seekpoints))

    # Debug info
    print("Rhombus responded with ")
    print(response)
