from typing import List, Dict

import RhombusAPI as rapi

from rhombus_types.human_event import HumanEvent
from rhombus_types.vector import Vec2
from rhombus_types.camera import Camera

def get_human_events(api_client: rapi.ApiClient, camera: Camera, start_time: int, duration: int) -> Dict[int, List[HumanEvent]]:
    """Get human events from a camera
    
    :param api_client: The API Client for sending requests to Rhombus
    :param camera: The camera to get the human events for
    :param start_time: The start time in seconds to start getting human events
    :param duration: The duration in seconds of time since the start time to look for events
    :return: Returns a map of object ID to HumanEvent array 
    """

    # Create the api
    api = rapi.CameraWebserviceApi(api_client=api_client)

    # Create a map of ID to bounding box to hold the result
    ids: Dict[int, List[rapi.FootageBoundingBoxType]] = dict()

    # Send the request to Rhombus to get the bounding boxes
    get_footage_bounding_box_request = rapi.CameraGetFootageBoundingBoxesWSRequest(camera_uuid=camera.uuid, start_time=start_time, duration=duration)
    res = api.get_footage_bounding_boxes(body=get_footage_bounding_box_request)

    # Filter the resulting bounding boxes so that we only get human events
    raw_events: List[rapi.FootageBoundingBoxType] = filter(lambda event: event.a == rapi.ActivityEnum.MOTION_HUMAN, res.footage_bounding_boxes)

    # Loop through all of the raw events
    for event in raw_events:
        # If for whatever reason the timestamp is before our start time, then don't include it.
        # This really shouldn't be necessary, but it seems sometimes the API gets confused and sends back some bounding boxes before the start time.
        # Either that or I'm doing something wrong, probably the latter tbh
        if event.ts < start_time * 1000: 
            continue

        if event.object_id not in ids:
            ids[event.object_id] = [event]
        else:
            ids[event.object_id].append(event)
    
    events: Dict[int, List[HumanEvent]] = dict()

    for object_id in ids:
        boxes = ids[object_id]

        for box in boxes:

            if box.r - box.l < 0.02:
                continue
            if box.b - box.t < 0.02:
                continue

            dimensions = Vec2((box.r - box.l) / 10000, (box.b - box.t) / 10000)

            position = Vec2((box.r + box.l) / 2 / 10000, (box.b + box.t) / 2 / 10000)

            event = HumanEvent(id=box.object_id, position=position, dimensions=dimensions, timestamp=box.ts, camera=camera)

            if box.object_id not in events:
                events[box.object_id] = [event]
            else:
                events[box.object_id].append(event)
                

    for boxes in events.values():
        boxes.sort(key=lambda human_event: human_event.timestamp)

    return events
