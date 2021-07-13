from typing import Dict, List
from rhombus_types.human_event import HumanEvent
from rhombus_environment.environment import Environment

def isolate_edge_events(all_events: Dict[int, List[HumanEvent]]) -> Dict[int, List[HumanEvent]]:
    """Isolates events and only returns events that are at the edge of the camera's viewport

    :param all_events: A map of objectID to human event list
    :return: Returns the resulting vector [a.x + b.x, a.y + b.y] 
    """

    # Create a new map for our edge events
    edge_events: Dict[int, List[HumanEvent]] = dict()

    # Loop through all of the events
    for id in all_events:
        # The last event is what matters for us, since this isolator is only used for the exit event detection pipeline
        events = all_events[id]
        event = events[len(events) - 1]

        # Edge values
        small_edge = Environment.get().edge_event_detection_distance_from_edge
        large_edge = 1 - Environment.get().edge_event_detection_distance_from_edge

        # If the position of the event is above our threshold, then we can add the events to our edge events map
        if event.position[1] < small_edge or event.position[1] > large_edge or event.position[0] < small_edge or event.position[0] > large_edge:
            edge_events[id] = events


    # Return the edge events
    return edge_events


