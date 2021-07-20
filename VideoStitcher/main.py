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

import math

# Import sys and argparse for cmd args
import sys

# Import requests to create our http client
import requests

sys.path.append('../')

# Import RhombusAPI to create our Api Client
import RhombusAPI as rapi

# Import our connection type
from rhombus_types.connection_type import ConnectionType

# Import some logging utilities
from logging_utils.colors import LogColors

# Import all of our services which will do the heavy lifting
from rhombus_environment.environment import Environment
from rhombus_services.camera_list import get_camera_list
from rhombus_services.prompt_user import prompt_user
from pipeline.detection_pipeline import detection_pipeline
from pipeline.related_events_pipeline import related_events_pipeline
from pipeline.related_event_isolator_pipeline import related_event_isolator_pipeline
from pipeline.clip_combiner_pipeline import clip_combiner_pipeline


class Main:
    """Entry point class, which handles all of the execution of requests and processing of object detection

    :attribute __api_key: The Api Key that is specified when running the application
    :attribute __connection_type: The ConnectionType that is specified when running the application
    :attribute __api_client: The RhombusAPI client that will be used throughout the lifetime of our application
    :attribute __http_client: The HTTP Client that will be used for fetching clips throughout the lifetime of our application
    """

    __api_key: str
    __api_client: rapi.ApiClient
    __connection_type: ConnectionType
    __http_client: requests.sessions.Session

    def __init__(self) -> None:
        """Constructor for the Main class, which will initialize all of the clients and arguments

        :param args: The parsed user cmd arguments
        """

        # Save the cmd args in our runner
        self.__api_key = Environment.get().api_key

        # Create an API Client and Configuration which will be used throughout the program
        config: rapi.Configuration = rapi.Configuration()
        config.api_key['x-auth-apikey'] = self.__api_key

        # We need to set the additional header of x-auth-scheme, otherwise we will receive 401
        self.__api_client = rapi.ApiClient(configuration=config, header_name="x-auth-scheme", header_value="api-token")

        # By default the connection type is LAN, unless otherwise specified by the user
        self.__connection_type = ConnectionType.LAN

        # If the user specifies -t WAN, then we need to run in WAN mode, however this is not recommended
        if (Environment.get().connection_type == "WAN"):
            self.__connection_type = ConnectionType.WAN
            print(
                LogColors.WARNING + "Running in WAN mode! This is not recommended if it can be avoided." + LogColors.ENDC)

        # Create an HTTP client
        self.__http_client = requests.sessions.Session()

    def execute(self):
        """Entry Point"""
        # Get a list of available cameras
        cam_list = get_camera_list(self.__api_client)

        # Get the selected event
        selected_event = prompt_user(api_client=self.__api_client, cameras=cam_list)

        # Check for error when getting user input
        if selected_event == None:
            print("Invalid input!")
            return

        res = detection_pipeline(self.__api_client, selected_event.camera, selected_event.object_id, math.floor(selected_event.timestamp / 1000))
        
        # If there are more than one exit event found, that means we can continue
        if len(res) > 0:
            # Look for related events
            events = related_events_pipeline(self.__api_client, res, cam_list)

            # Then isolate those related events
            events = related_event_isolator_pipeline(events)

            # If there were any finalized events found
            if len(events) > 0:
                # Loop through them
                for event in events:

                    # Final check to make sure there is at least one related event attached
                    if event.following_event != None:
                        clip_combiner_pipeline(api_key=self.__api_key, http_client=self.__http_client, api_client=self.__api_client, type=self.__connection_type, event=event)


if __name__ == "__main__":
    # Start the main runner
    Main().execute()
