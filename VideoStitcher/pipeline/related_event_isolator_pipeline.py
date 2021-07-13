from typing import Union, cast, List
from rhombus_types.events import EnterEvent, ExitEvent, FinalizedEvent, events_are_the_same
from pipeline.pipeline_services.event_collator import can_collate_events, do_collate_enter_and_exit

def internal_finalize_event(event: Union[EnterEvent, ExitEvent, None]) -> Union[FinalizedEvent, None]:
    """Recursively creates finalized events based on an EnterEvent | ExitEvent

    :param event: The event to recursively create a finalized event from
    :return: Returns a finalized event based on the provided enter/exit event
    """

    # If we reach the end of our recursion, return None because this will set the finalized event `following_event` member as None, which will indicate the end of a chain
    if event == None: 
        return None

    # Get the list of events
    events = event.events

    # Return a finalized event
    return FinalizedEvent(
                id=event.id,
                start_time=events[0].timestamp,
                end_time=events[len(events) - 1].timestamp,
                data=events,
                # We only want to set a following event, if the `event` is an `ExitEvent`. Otherwise we want it to be None. We will use the exit event's first related event as the following event
                following_event=(internal_finalize_event(cast(ExitEvent, event).related_events[0]) if isinstance(event, ExitEvent) else None)
            )

def finalize_exit_events(exit_events: List[ExitEvent]) -> List[FinalizedEvent]:
    """Finalizes exit events to be used for the dev tools and when combining clips

    :param exit_events: The array of exitEvents to finalize
    :return: Returns the finalized versions of all of the provided exit events 
    """

    # Create our array of finalized events
    final_events: List[FinalizedEvent] = list()

    # Loop through all of the exit events
    for exit_event in exit_events:
        

        # Create the finalized events
        finalized = internal_finalize_event(exit_event)
        
        # finalized will never really be None, but this is just to get around the python type checker
        if finalized != None:
            final_events.append(finalized)

    return final_events

def related_event_isolator_pipeline(exit_events: List[ExitEvent]) -> List[FinalizedEvent]:
    """Isolates related events and finalizes them

    :param exit_events: The array of exit events which will be finalized
    :return: Returns the finalized events 
    """

    # Loop through all of the exit events starting from the end
    for i in range(len(exit_events) - 1, -1, -1):
        current_exit_event = exit_events[i]

        # Loop through all of the related events attached to the currentExitEvent
        for j in range(0, len(current_exit_event.related_events)):
            current_related_event = current_exit_event.related_events[j]

            # Loop through all of the exit events that follow the currentExitEvent
            #
            # Here we will attempt to chain any exit events following currentExitEvent to currentRelatedEvent
            for k in range(i + 1, len(exit_events)):
                other_exit_event = exit_events[k]

                if can_collate_events(current_related_event, other_exit_event):
                    # If the currentRelatedEvent and the otherExitEvent can be collated, as in the currentRelatedEvent and otherExitEvent reasonably follow a pattern 
                    # that looks like they are related.

                    # Then do a collation between the two
                    exit_events[i].related_events[j] = do_collate_enter_and_exit(current_related_event, other_exit_event)

                    # And remove the extraneous exit event
                    del exit_events[k]

                    # Nothing more to do with any other following exit events so we will break
                    break

                elif events_are_the_same(current_related_event, other_exit_event):
                    # If the currentRelatedEvent and the otherExitEvent are the same, as in they are literally the same event

                    # Then just set the related event as otherExitEvent (so that it has any relatedEvents that are attached to otherExitEvent)
                    exit_events[i].related_events[j] = other_exit_event

                    # And remove the extraneous exit event
                    del exit_events[k]

                    # Nothing more to do with any other following exit events so we will break
                    break


    # Finalize the exit events
    res = finalize_exit_events(exit_events)

    # Then return our data
    return res


