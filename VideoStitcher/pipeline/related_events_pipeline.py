from typing import List

import RhombusAPI as rapi

from rhombus_types.events import ExitEvent, EdgeEventsType, enter_events_from_map
from rhombus_types.camera import Camera
from rhombus_services.human_event_service import get_human_events
from pipeline.isolators import velocity_isolator, event_length_isolator

def related_events_pipeline(api_client: rapi.ApiClient, exit_events: List[ExitEvent], cameras: Camera[]) -> List[ExitEvent]: 
    """Looks through human events that could be related to our exit event to find a suitable match

    :param api_client: The API Client for sending requests to Rhombus
    :param camera: The Camera to look for human events
    :param object_id: The object ID to look for
    :param timestamp: The timestamp at which to look for human events 
    :return: Returns an array of exit events that match the object ID
    """
    
