from typing import Dict, List

import RhombusAPI as rapi

import functools

from rhombus_types.events import ExitEvent, EdgeEventsType, exit_events_from_map
from rhombus_services.human_event_service import get_human_events
from rhombus_environment.environment import Environment
from pipeline.isolators.edge_event_isolator import isolate_edge_events
from pipeline.isolators.velocity_isolator import isolate_velocities
from pipeline.isolators.event_length_isolator import isolate_events_from_length
from rhombus_types.camera import Camera
from rhombus_types.events import compare_events

def filter_human_events_by_object_id(event: ExitEvent, object_id: int) -> bool:
    """Function used to filter a list of events so that only ones containing an objectID remain

    :param event: The HumanEvent to check
    :param object_id: The ObjectID to check for
    """

    for human_event in event.events:
        if human_event.id == object_id:
            return True

    return False

def detection_pipeline(api_client: rapi.ApiClient, camera: Camera, object_id: int, timestamp: int) -> List[ExitEvent]:
    """Parses through human events to find exit events
    
    :param api_client: The API Client for sending requests to Rhombus
    :param camera: The camera to look for human events
    :param object_id: The object ID to look for
    :param timestamp: The timestamp at which to look for human events
    :return: Returns an array of exit events that match the object ID
    """

    # Get the duration of time in seconds to look for human events. This is by default 10 minutes.
    duration: int = round(Environment.get().exit_event_detection_duration_seconds)

    # A small offset in seconds is good so that we don't accidentally barely miss the object ID. This is by default 30 seconds.
    offset: int = round(Environment.get().exit_event_detection_offset_seconds)

    # Get an array of human events within the timeframe
    res = get_human_events(api_client=api_client, camera=camera, start_time=timestamp - offset, duration=duration)

    print(str(len(res)) + " humans found")

    # Isolate the human events by length
    isolated_events = isolate_events_from_length(res)

    print(str(len(isolated_events)) + " were found from length and object IDs")

    # Isolate the human events by edge and then by length 
    edge_events = isolate_events_from_length(isolate_edge_events(isolated_events))

    print(str(len(edge_events)) + " were found from velocity")

    # Isolate the human events by velocity
    exit_events = isolate_velocities(edge_events, EdgeEventsType.End)

    print(str(len(exit_events)) + " were found from velocity")

    # Convert our raw map of objectID to HumanEvent[] to an array of ExitEvents
    events =  exit_events_from_map(exit_events)

    # Only include exit events that actually contain our object ID
    filter(lambda event: filter_human_events_by_object_id(event, object_id), events)

    # Sort all of the events by time
    events.sort(key=functools.cmp_to_key(compare_events))

    # Sort all of the related events also
    for e in events:
        e.related_events.sort(key=functools.cmp_to_key(compare_events))
    return events
