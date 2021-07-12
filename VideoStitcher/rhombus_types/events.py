# Import type hints
from typing import List, Dict

import numpy as np

from rhombus_utils.velocity import get_velocity
from rhombus_types.human_event import HumanEvent
from rhombus_types.vector import Vec2, validate_vec2

from enum import Enum, auto

class EdgeEventsType(Enum):
    """Enum to specify whether an edge event occurs at the beginning or the end"""
    Begin = auto()
    End = auto()

class EnterEvent:
    """This is represents an event where someone walks into view of a the camera, either from the top, bottom, left, or right.

    :attribute id: The ObjectID of this enter event. 
    :attribute events: The array of human events that are attached to this enter event
    :attribute velocity: The X and Y velocity in permyriad position of the box / milisecond.
                         This is just the velocity of the bounding box, it is not really a good indicator of the velocity of the real object,
                         but we use it regardless for the isolation of different events
    """

    id: int
    events: List[HumanEvent]
    velocity: np.ndarray

    def __init__(self, id: int, events: List[HumanEvent], velocity: np.ndarray):
        """Constructor for an EnterEvent

        :param id: The ObjectID of this enter event.
        :param events: The array of human events that are attached to this enter event
        :param velocity: The X and Y velocity in permyriad position of the box / milisecond.
        """

        self.id = id
        self.events = events
        self.velocity = velocity

class ExitEvent(EnterEvent):
    """This is represents an event where someone walks out of view of a camera, either from the top, bottom, left, or right.

    :attribute related_events: The array of related enter events that could follow this exit event.
                               This type is used at a stage in isolation where we cannot be sure which of these enter events best match for this exit event, which is why this is an array. 
                               This member is best characterized as any enter events which could possibly be related to this exit event
    """

    related_events: List[EnterEvent]

    def __init__(self, id: int, events: List[HumanEvent], velocity: np.ndarray, related_events: List[EnterEvent]):
        """Constructor for an ExitEvent

        :param id: The ObjectID of this exit event.
        :param events: The array of human events that are attached to this exit event
        :param velocity: The X and Y velocity in permyriad position of the box / milisecond.
        """

        EnterEvent.__init__(self, id, events, velocity)
        self.related_events = related_events 

class FinalizedEvent:
    """A finalized event is the final output of the detection pipeline.
    It is an event where a human was detected leaving, and there were one or more following enter and exit events 
    which can reasonably be assumed to be the same person walking into view or out of view of another camera

    :attribute id: The ObjectID of this enter event.
    :attribute data: The array of human events that are attached to this finalized event
    :attribute following_event: A finalized event (either enter or exit) which are related.
                                For example, if this event was of someone leaving the camera, the followingEvent could be when someone enters the camera.
                                This member could also be undefined if there is no following event
    :attribute start_time: The time in miliseconds of the first event in `data`.
    :attribute end_time: The time in miliseconds of the last event in `data`.
    """

    id: int
    data: List[HumanEvent]
    following_event: 'FinalizedEvent'
    start_time: int
    end_time: int

    def __init__(self, id: int, data: List[HumanEvent], following_event: 'FinalizedEvent', start_time: int, end_time: int):
        """Constructor for a finalized event

        :param id: The ObjectID of this enter event.
        :param data: The array of human events that are attached to this finalized event
        :param following_event: A finalized event (either enter or exit) which are related.
                                For example, if this event was of someone leaving the camera, the followingEvent could be when someone enters the camera.
                                This member could also be undefined if there is no following event
        :param start_time: The time in miliseconds of the first event in `data`.
        :param end_time: The time in miliseconds of the last event in `data`.
        """

        self.id = id
        self.data = data
        self.following_event = following_event
        self.start_time = start_time
        self.end_time = end_time


def compare_human_events_by_time(a: HumanEvent, b: HumanEvent) -> int:
    """Compares 2 human events based on their timestamps

    :param a: The first human event
    :param b: The second human event
    :return: Returns -1 if `a` is before `b`, 1 if `b` is before `a`, and 0 if `a` and `b` occur at the same time
    """

    if a.timestamp < b.timestamp:
        return -1
    if a.timestamp > b.timestamp:
        return 1
    return 0


def compare_events(a: EnterEvent, b: EnterEvent) -> int:
    """Compares 2 Enter events based on the timestamp of the first human event

    :param a: The first enter event
    :param b: The second enter event
    :return: Returns -1 if `a` is before `b`, 1 if `b` is before `a`, and 0 if `a` and `b` occur at the same time
    """

    return compare_human_events_by_time(a.events[0], b.events[0])

def enter_events_from_map(events: Dict[int, List[HumanEvent]]) -> List[EnterEvent]: 
    """Gets a list of enter events from a map of raw human events

    :param events: The map of objectID to raw human event array
    :return: Returns the list of EnterEvents that correspond to the map of human events
    """

    # Create our array of resulting events
    result_events: List[EnterEvent] = list()

    # Loop through all of the events
    for object_id in events:
        # Get our events
        es = events[object_id]

        # Push an EnterEvent for each of our resulting events
        result_events.append(
                    EnterEvent(
                        # The ID will be our key in our map
                        id=object_id,
                        # The events will be the value in our map
                        events=es,
                        # The velocity will just be the velocity between the first event and the second, since this is an enter event and that's the only velocity we really care about
                        velocity=get_velocity(es[0], es[1]),
                    ),
        )

    # Sort the resulting events based on their timestamp
    result_events.sort(key=lambda event: event.events[0].timestamp)

    # Return the resulting enter events
    return result_events

def exit_events_from_map(events: Dict[int, List[HumanEvent]]) -> List[ExitEvent]: 
    """Gets a list of exit events from a map of raw human events

    :param events: The map of objectID to raw human event array
    :return: Returns the list of ExitEvents that correspond to the map of human events
    """

    # Create our array of resulting events
    result_events: List[ExitEvent] = list()

    # Loop through all of the events
    for object_id in events:
        # Get our events
        es = events[object_id]

        # Push an EnterEvent for each of our resulting events
        result_events.append(
                    ExitEvent(
                        # The ID will be our key in our map
                        id=object_id,
                        # The events will be the value in our map
                        events=es,
                        # The velocity will just be the velocity between the first event and the second, since this is an enter event and that's the only velocity we really care about
                        velocity=get_velocity(es[0], es[1]),
                        # The related events will be empty because we don't have that information, this will be updated later in the program
                        related_events=[],
                    ),
        )

    # Sort the resulting events based on their timestamp
    result_events.sort(key=lambda event: event.events[0].timestamp)

    # Return the resulting enter events
    return result_events


def events_are_the_same(a: EnterEvent, b: EnterEvent) -> bool:
    """Determines if two enter or exit events are the same, based on the timestamp, camera UUID, the dimensions of the box, and the position.
       NOTE: We don't compare the object ID because this value is not very accurate.

    :param a: The first enter event
    :param b: The second enter event
    :return: Returns true if both of the events are the same
    """

    a_first = a.events[0]
    b_first = b.events[0]

    return a_first.timestamp == b_first.timestamp and a_first.camera.uuid == b_first.camera.uuid and a_first.dimensions == b_first.dimensions and a_first.position == b_first.position

def exit_event_is_related(event: ExitEvent, previous_event: ExitEvent) -> bool:
    """Determines if two exit events are somehow related, in that the related event of one is the same as the our own one. This is used for chaining exit events together.
       For example if one exit event has a related event that matches another exit event, then we will assume that the first exit event has a related event which is our second exit event,
       thus chaining exit event 2 to exit event 1

    :param event: An exit event
    :param previous_event: The exit event that occurs before `event`
    :return: Returns true if `event` can be changed to `previous_event`
    """

    # Loop through all of the related events of `previous_event`
    for related_event in previous_event.related_events:
        # If the exit events are the same, then we will return true because `event` can be chained to `previous_event`
        if events_are_the_same(related_event, event):
            return True

    # If none of the related events of `previous_event` match `event`, then `event` cannot be chained to `previous_event`
    return False
