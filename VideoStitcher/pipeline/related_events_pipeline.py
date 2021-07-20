###################################################################################
# Copyright (c) 2021 Rhombus Systems                                              #
#                                                                                 # 
# Permission is hereby granted, free of charge, to any person obtaining a copy    #
# of this software and associated documentation files (the "Software"), to deal   #
# in the Software without restriction, including without limitation the rights    #
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell       #
# copies of the Software, and to permit persons to whom the Software is           #
# furnished to do so, subject to the following conditions:                        #
#                                                                                 # 
# The above copyright notice and this permission notice shall be included in all  #
# copies or substantial portions of the Software.                                 #
#                                                                                 # 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR      #
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,        #
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE     #
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER          #
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,   #
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE   #
# SOFTWARE.                                                                       #
###################################################################################

from typing import List

import RhombusAPI as rapi
import math

from rhombus_types.events import ExitEvent, EdgeEventsType, enter_events_from_map
from rhombus_types.camera import Camera
from rhombus_services.human_event_service import get_human_events
from rhombus_environment.environment import Environment
from pipeline.isolators.velocity_isolator import isolate_velocities
from pipeline.isolators.event_length_isolator import isolate_events_from_length
from rasterization.rasterizer import get_valid_cameras

def related_events_pipeline(api_client: rapi.ApiClient, exit_events: List[ExitEvent], cameras: List[Camera]) -> List[ExitEvent]: 
    """Looks through human events that could be related to our exit event to find a suitable match

    :param api_client: The API Client for sending requests to Rhombus
    :param camera: The Camera to look for human events
    :param object_id: The object ID to look for
    :param timestamp: The timestamp at which to look for human events 
    :return: Returns an array of exit events that match the object ID
    """
    for event in exit_events:    
        # Get a list of valid cameras based on the position of the exit event
        _cameras: List[Camera] = get_valid_cameras(cameras, event, Environment.get().pixels_per_meter, Environment.get().capture_radius_meters)

        print("Looking through cameras")

        for camera in _cameras:
            print(camera.uuid)

        # Get the events
        events = event.events

        # Get the startTime
        start_time = math.floor(events[len(events) - 1].timestamp / 1000)

        # Get the duration in seconds of how far in the future to look for related human events
        detection_duration = Environment.get().related_event_detection_duration_seconds

        # Loop through all of the cameras that are valid
        for other_cam in _cameras:
            # Get the human events and isolate them from length
            other_human_events = get_human_events(api_client, other_cam, start_time, detection_duration)

            # Collate the events and isolate them from length
            collated_events = isolate_events_from_length(other_human_events)

            # Isolate the events based on their velocities
            velocity_events = isolate_velocities(collated_events, EdgeEventsType.Begin)

            print("Found " + str(len(velocity_events)) + " related events for camera " + other_cam.uuid)

            # Add the related enter events to the exit event
            event.related_events = event.related_events + enter_events_from_map(velocity_events)

    # Return the exit events
    return exit_events
