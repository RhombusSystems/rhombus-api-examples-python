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

from typing import List, Dict, Union
import RhombusAPI as rapi

from rhombus_types.camera import Camera
from rhombus_services.human_event_service import get_human_events
from pipeline.isolators.event_length_isolator import isolate_events_from_length
from rhombus_environment.environment import Environment

import time

class RecentHumanEventInfo:
    """Holds information about a recent human event

    :attribute timestamp: The timestamp in miliesconds of this human event
    :attribute object_id: The ObjectID of the HumanEvent
    :attribute camera: The camera of this HumanEvent
    """

    timestamp: int
    object_id: int
    camera: Camera

    def __init__(self, timestamp: int, object_id: int, camera: Camera):
        """Constructor for a recent human event
        
        :param timestamp: The timestamp in miliesconds of this human event
        :param object_id: The ObjectID of the HumanEvent
        :param camera: The camera of this HumanEvent
        """

        self.timestamp = timestamp
        self.object_id = object_id
        self.camera = camera

def print_recent_human_events(api_client: rapi.ApiClient, events: List[RecentHumanEventInfo], cameras: List[Camera]) -> None:
    """Prints a list of human events to the console so that the user can choose one


    :param api_client: The API Client for sending requests to Rhombus
    :param events: The array of recent human events.
    :param cameras: The array of available cameras.
    """

    # Create the API
    api = rapi.CameraWebserviceApi(api_client=api_client)

    # Declare the base frame URIs for use later. These URIs in combination with the recent human event info will give us URLs to image frames of recent human events.
    base_frame_uris: Dict[str, str] = dict()

    # Loop through all of the cameras
    for cam in cameras:

        # Get the media URI of that camera
        media_uri_request = rapi.CameraGetMediaUrisWSRequest(camera_uuid=cam.uuid)
        res = api.get_camera_media_uris(body=media_uri_request)

        # Get the URI Template
        vod_uri: str = res.wan_vod_mpd_uri_template
        
        # Create our base frame URI in our map to our cam UUID for easy access later.
        base_frame_uris[cam.uuid] = vod_uri[:vod_uri.find("/dash")] + "/media/frame/"


    print("Here are the recent human events in the last 10 minutes: ")

    # Loop through all of the events
    i = 0
    for event in events:
        # Now get our frame URI to present to the user.
        frame_uri = base_frame_uris[event.camera.uuid] + event.camera.uuid + "/" + str(event.timestamp) + "/thumb.jpeg"

        # And print out the url and other relevant info
        print("(" + str(i) + ") URL: " + frame_uri + "\n Object ID: " + str(event.object_id) + "\n Timestamp: " + str(event.timestamp) + "\n CameraUUID: " + event.camera.uuid)
        print("--------------------------------------")
        i += 1


def prompt_user(api_client: rapi.ApiClient, cameras: List[Camera]) -> Union[RecentHumanEventInfo, None]:
    """Prompts a user for which person they would like to follow in the program.

    :param api_client: The API Client for sending requests to Rhombus
    :param cameras: The array of available cameras
    :return: Returns a recent human event that will be used for the program.
    """

    # Create an array where we will put our recent human events
    recent_human_events: List[RecentHumanEventInfo] = list()

    # The duration in seconds in the past to look for recent human events
    duration = Environment.get().suggested_human_event_seconds_since_current_time

    # The starting time in seconds (hence the /1000) since epoch where we will start looking for human events
    current_time = round(time.time()) - duration

    # Loop through all of the cameras
    for cam in cameras:
        # Get a list of human events
        human_events = get_human_events(api_client, cam, current_time, duration)

        # Collate and isolate the events from length
        collated_events = isolate_events_from_length(human_events);

        # Loop through each of the collated events
        for es in collated_events.values():
            # We only really care about the first of those human event arrays
            event = es[0]

            # Add the recent human event to our array
            recent_human_events.append(RecentHumanEventInfo(timestamp=event.timestamp, object_id=event.id, camera=event.camera))

    # Now we are going to print that information to the user
    print_recent_human_events(api_client, recent_human_events, cameras)
    
	# If there are any recent human events, we will ask the user to choose one from the printed events.
	# Otherwise if there aren't any human events then we will just set our selection as -1, meaning that we want to manually specify.
    auto_select_response: int = -1 if len(recent_human_events) == 0 else int(input("Please select a human event to follow. You can either use one of the events in the last 10 minutes OR you can type -1 to specify manually a custom objectID, timestamp, and camera. > "))
    
    if auto_select_response < 0 or auto_select_response >= len(recent_human_events):
        object_id = int(input("Object ID of the person you would like to follow > "))

        timestamp = int(input("Timestamp in miliseconds at which to start looking for this person > "))

        camera_uuid = str(input("The camera UUID in which this person appears first > "))

        camera: Union[Camera, None] = None
        
        for cam in cameras:
            if cam.uuid == camera_uuid:
                camera = cam
                break

        if camera is None:
            print("Camera UUID not found!")
            return None

        return RecentHumanEventInfo(object_id=object_id, timestamp=timestamp, camera=camera)
    else:
        return recent_human_events[auto_select_response]

