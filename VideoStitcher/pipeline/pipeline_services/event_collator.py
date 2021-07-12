from typing import List
import numpy as np
from rhombus_types.events import  EnterEvent, ExitEvent
from rhombus_types.human_event import HumanEvent
from rhombus_utils.velocity import get_velocity
from rhombus_types.vector import vec2_compare, vec2_len

def can_collate_events(a: EnterEvent, b: EnterEvent) -> bool:
    """Checks whether two events follow the pattern that `b` follows `a` in such a way that makes it seem like they are connected and can be combined

    :param a: First event to check
    :param b: Second event to check
    :return: Returns true if the events can be combined since they are similar
    """

    
    a_event = a.events[len(a.events) - 1]
    b_event = b.events[0]

    # Get the time delta in miliseconds between the last human event of `a` to the first human event of `b`
    time_delta = b_event.timestamp - a_event.timestamp

    # If the camera UUID is the same, the time delta is withing 5 seconds, and the positions are nearly identical, then we can assume that the events can be collated
    if a_event.camera.uuid == b_event.camera.uuid and time_delta < 5000 and time_delta > 0 and  vec2_compare(np.absolute(np.subtract(a_event.position,  b_event.position)), 0.1) == 1:
        return True

    # Another check we will do is based on velocity
    # We will get the velocity between the last 2 events of `a`
    a_velocity = get_velocity(a_event, a.events[len(a.events) - 2])
    # And the velocity between the first 2 events of `b`
    b_velocity = get_velocity(b.events[1], b_event)

    # We will also get the velocity between `a` and `b`
    velocity_between = get_velocity(a_event, b_event)

    # Make sure that the velocity of `a` and `b` are almost the same (within a 0.1 threshold which is extremely generous)
    velocity_a_and_b_similar = vec2_compare(np.subtract(a_velocity, b_velocity), 0.1) == 1

    # Make sure that the velocity between `a` and `b` is similar to the velocities of the end of `a` and the beginning of `b` (within a 0.1 threshold which is extremely generous).
    # On a graph this will look like 2 lines that have a break in the middle but the middle section looks like a continuation of the line. 
    velocity_between_and_a_similar = vec2_compare(np.subtract(velocity_between, a_velocity), 0.1) == 1
    velocity_between_and_b_similar = vec2_compare(np.subtract(velocity_between, b_velocity), 0.1) == 1

    if velocity_a_and_b_similar and velocity_between_and_a_similar and velocity_between_and_b_similar:
        # If everything with the velocities checks out, then return
        return True

    # Otherwise return false
    return False


def do_collate_enter_and_exit(a: EnterEvent, b: ExitEvent) -> ExitEvent:
    """Combines Human Events that are similar, even if object IDs do not match

    :param a: The enter event to combine the exit event with 
    :param b: The exit event to combine the enter event with
    :return: Returns a combined exit event that has the events of both enter event `a` and exit event `b`
    """
    
    # The events will consist of both of the events of `a` and `b`. These will also be sorted by timestamp.
    collated_events: List[HumanEvent] = a.events + b.events
    collated_events.sort(key=lambda human_event: human_event.timestamp)

    # Return our new collated event
    return ExitEvent(events=collated_events, id=b.id, related_events=b.related_events, velocity=b.velocity)
