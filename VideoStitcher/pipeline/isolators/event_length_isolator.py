from typing import Dict, List
from rhombus_types.human_event import HumanEvent
from rhombus_environment.environment import Environment

def isolate_events_from_length(events: Dict[int, List[HumanEvent]]) -> Dict[int, List[HumanEvent]]:
    """Isolates events and only returns events that have a minimum number of events

    :param events: A map of objectID to human event list
    :return: Returns only events that have at least `Environment.get().minimum_event_length` events
    """

    # Loop through all of the events
    for id in list(events.keys()):
        es = events[id]

        # If the number of events does not pass the threshold, then delete them
        if len(es) < Environment.get().minimum_event_length: 
            del events[id]

    return events

