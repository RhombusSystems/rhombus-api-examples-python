# Import type hints
from typing import List

# Import sys and argparse for cmd args
import sys
import argparse

import json

# Import requests to create our http client
import requests

# Import timeit so that we can time execution time
from timeit import default_timer as timer

# Import time so that we can sleep
import time

sys.path.append('../')

# Import RhombusAPI to create our Api Client
import RhombusAPI as rapi

# Import our connection type
from rhombus_types.connection_type import ConnectionType
from rhombus_types.events import ExitEvent

# Import some logging utilities
from logging_utils.colors import LogColors

# Import all of our services which will do the heavy lifting
from rhombus_services.media_uri_fetcher import fetch_media_uris
from rhombus_services.vod_fetcher import fetch_vod
from rhombus_services.arg_parser import parse_arguments
from rhombus_services.camera_list import get_camera_list
from rhombus_services.human_event_service import get_human_events
from rhombus_services.prompt_user import prompt_user


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

    def __init__(self, args: argparse.Namespace) -> None:
        """Constructor for the Main class, which will initialize all of the clients and arguments

        :param args: The parsed user cmd arguments
        """

        # Save the cmd args in our runner
        self.__api_key = args.api_key

        # Create an API Client and Configuration which will be used throughout the program
        config: rapi.Configuration = rapi.Configuration()
        config.api_key['x-auth-apikey'] = self.__api_key

        # We need to set the additional header of x-auth-scheme, otherwise we will receive 401
        self.__api_client = rapi.ApiClient(configuration=config, header_name="x-auth-scheme", header_value="api-token")

        # By default the connection type is LAN, unless otherwise specified by the user
        self.__connection_type = ConnectionType.LAN

        # If the user specifies -t WAN, then we need to run in WAN mode, however this is not recommended
        if (args.connection_type == "WAN"):
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

if __name__ == "__main__":
    # Get the user's arguments
    args = parse_arguments(sys.argv[1:])

    # Start the main runner
    Main(args).execute()
