from typing import Dict, List
from rhombus_types.human_event import HumanEvent

def isolate_events_from_length(events: Dict[int, List[HumanEvent]]) -> Dict[int, List[HumanEvent]]:
    """Isolates events and only returns events that have a minimum number of events

    :param events: A map of objectID to human event list
    :return: Returns only events that have at least `Environment.MinimumEventLength` events
    """

    # Loop through all of the events
    for id in events:
        es = events[id]

        # If the number of events does not pass the threshold, then delete them
        if len(es) < 2: 
            del events[id]

    return events

