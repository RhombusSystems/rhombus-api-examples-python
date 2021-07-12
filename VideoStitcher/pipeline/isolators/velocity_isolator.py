from typing import Dict, List

from rhombus_types.human_event import HumanEvent
from rhombus_types.events import EdgeEventsType
from rhombus_utils.velocity import normalize_velocity, normalize_position, get_velocity
from rhombus_types.vector import Vec2, vec2_compare
import numpy as np
import math as math

def isolate_velocities(events: Dict[int, List[HumanEvent]], type: EdgeEventsType) -> Dict[int, List[HumanEvent]]:
    """Isolates events and only returns events that pass a certain minimum velocity and have a direction that matches the edge location of the event

    :param events: A map of objectID to human event list    
    :param type: Whether or not we are isolating based on enter or exit events
    :return: Returns only events that pass a certain minimum velocity and have a direction that matches the edge location of the event
    """

    # Loop through all of the events
    for id in events:
        es = events[id]

        # Declare our velocity
        velocity: np.ndarray 

        # Get our beginning and final events
        begin_event = es[0]
        final_event = es[len(es) - 1]

        # We will get the velocities between the human events and store them here.
        # These will later be ranked and we will come out with a final average velocity.
        velocities: List[np.ndarray] = list()

        if type == EdgeEventsType.Begin:
            # If we are looking for begin events, start from the beginning and get all of the velocities up to 4 elements or until we run out of human events to get velocities for
            for i in range(1, min(4, len(es))):
                # We will get the previous event
                previous_event = es[i - 1]

                # And the current event
                current_event = es[i]

                # And get the velocity between these two human events
                velocity = get_velocity(previous_event, current_event)

                # Then add the velocity to the array
                velocities.append(velocity)

        elif type == EdgeEventsType.End:
            # If we are looking for begin events, start from the end and get all of the velocities up to 4 elements or until we run out of human events to get velocities for
            for i in range(len(es) - 2, max(len(es) - 4, 0), -1):
                # We will get the following event
                following_event = es[i + 1]

                # And the current event
                current_event = es[i]

                # And get the velocity between the two
                velocity = get_velocity(current_event, following_event)

                # Then add the velocity to the array
                velocities.append(velocity)

        # If we have an even number of velocities, remove the last one so that we can properly rank
        if len(velocities) % 2 == 0:
            velocities.pop()

        # Next we are going to tally the number of positive and negative X direction velocities, see which one wins, then get the average X velocity based on that

        # We are going to count the number of negative and positive velocities for ranking
        neg_count = 0
        pos_count = 0

        # Loop through all of the velocities
        for i in range(0, len(velocities)):
            # Normalize the velocities
            normalized_velocity = normalize_velocity(velocities[i])

            if normalized_velocity[0] > 0:
                # If the normalized velocity is 1, increase the positive tally
                pos_count += 1

            elif normalized_velocity[0] < 0:
                # If the normalized velocity is -1, increase the negative tally
                neg_count += 1

            # If the normalized velocity is 0 then we won't worry about it.
            # This will almost never happen because there will almost certainly be differences in the bounding box position, even if small.
            # Since our threshold is just 0, there just needs to be any change in position AT ALL to consider it.

        # Figure out the winner, and use that as our check
        check = 1 if pos_count > neg_count else -1

        # Here we will accumulate our total velocity in the X axis
        total_velocity_x: float = 0

        # Loop through all of the velocities
        for velocity in velocities: 
            # Normalize the velocity
            normalized_velocity = normalize_velocity(velocity)

            # If the normalized velocity is the same as our check, that means that we will add it to our total velocity. 
            # For example if the check is 1 (meaning right) if the normalized velocity is also 1, then this velocity is also going right and we should consider it
            # We don't want to take the average of velocities that are going in the opposite direction. 
            # We only want to worry about the velocities that match the most common direction and use that as the average.
            if normalized_velocity[0] == check:
                total_velocity_x += velocity[0]

        # Finally here is our average velocity
        avg_velocity_x = total_velocity_x / max(pos_count, neg_count)

        # Reset the tally, and do the same thing on the Y axis
        neg_count = 0
        pos_count = 0

        # Loop through all of the velocities
        for i in range(0, len(velocities)):
            # Normalize the velocities
            normalized_velocity = normalize_velocity(velocities[i])

            if normalized_velocity[1] > 0:
                # If the normalized velocity is 1, increase the positive tally
                pos_count += 1
            elif normalized_velocity[1] < 0:
                # If the normalized velocity is -1, increase the negative tally
                neg_count += 1

            # If the normalized velocity is 0 then we won't worry about it.
            # This will almost never happen because there will almost certainly be differences in the bounding box position, even if small.
            # Since our threshold is just 0, there just needs to be any change in position AT ALL to consider it.

        # Figure out the winner, and use that as our check
        check = 1 if pos_count > neg_count else -1

        # Here we will accumulate our total velocity in the Y axis
        total_velocity_y: float = 0

        # Loop through all of the velocities
        for velocity in velocities:
            # Normalize the velocity
            normalized_velocity = normalize_velocity(velocity)

            # If the normalized velocity is the same as our check, that means that we will add it to our total velocity. 
            # For example if the check is 1 (meaning down) if the normalized velocity is also 1, then this velocity is also going down and we should consider it
            # We don't want to take the average of velocities that are going in the opposite direction. 
            # We only want to worry about the velocities that match the most common direction and use that as the average.
            if normalized_velocity[1] == check:
                total_velocity_y += velocity[1]

        # Finally here is our average velocity
        avg_velocity_y = total_velocity_y / max(pos_count, neg_count)

        # Our velocity is the two average velocities
        velocity = Vec2(avg_velocity_x, avg_velocity_y)

        # Next we will check to make sure that the magnitude abolute value of the velocity is greater than the threshold.
        if vec2_compare(np.absolute(velocity), 0.015 / 1000) == 1:
            # If the velocity doesn't meet the threshold then we will delete the event
            del events[final_event.id]

        else:
            # Get the normalized velocity
            normalized_velocity = normalize_velocity(velocity)

            # Next we need to make sure that the position of the human is on the edge of the screen is matches the velocity. If they are moving right, we want to make sure that 
            #
            # Because normalization will only give us a value of -1, 1, or 0, we can simply subtract the normalized position from the normalized velocity
            # to make sure that they velocity is in the same direction as the position on the edge.
            # 
            # For example, if our normalized position on the x axis is 1, that means that the person is near the right of the screen. 
            # We want to make sure that our velocity is going in the right direction. 
            # For a type of EdgeEventsType.End, this means that the normalized velocity is also going right, or 1.
            # For a type of EdgeEventsType.Begin, this means that the normalized velocity is going left, or -1.
            #
            # Based on these normalized values, we can simply subtract the normalized position from the normalized velocity to see that if it is an exit event it should be 0
            # and if it is an enter event it should NOT be 0
            #
            #
            # TLDR: Subtract the normalized position from the normalized velocity to make sure that it is going in the correct direction
            if type == EdgeEventsType.End:
                # If we are isolating based on exit events then we will normalize the position of the final event
                normalized_position = normalize_position(final_event.position, Vec2(0.4, 0.4))

                # Then we will compare the normalized position to the normalized velocity. Since this is an exit event we want these to match and thus be 0
                if normalized_velocity[0] - normalized_position[0] != 0 and normalized_velocity[1] - normalized_position[1] != 0:
                    del events[final_event.id]

            elif type == EdgeEventsType.Begin:
                # If we are isolating based on exit events then we will normalize the position of the final event
                normalized_position = normalize_position(begin_event.position, Vec2(0.5, 0.5))

                # Then we will compare the normalized position to the normalized velocity. Since this is an enter event we want these to match and thus NOT be 0
                if  normalized_velocity[0] - normalized_position[0] == 0 or normalized_velocity[1] - normalized_position[1] == 0:
                    del events[begin_event.id]


    # Return the events that made it
    return events
