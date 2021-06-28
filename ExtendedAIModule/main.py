# Import type hints
from typing import List

# Import sys and argparse for cmd args
import sys
import argparse

# Import requests to create our http client
import requests

# Import timeit so that we can time execution time
from timeit import default_timer as timer

# Import time so that we can sleep
import time

# Import OpenCV to create our client
import cv2

sys.path.append('../')

# Import RhombusAPI to create our Api Client
import RhombusAPI as rapi

# Import our connection type
from helper_types.connection_type import ConnectionType

# Import some logging utilities
from logging_utils.colors import LogColors

# Import all of our services which will do the heavy lifting
from rhombus_services.media_uri_fetcher import fetch_media_uris
from rhombus_services.vod_fetcher import fetch_vod
from rhombus_services.frame_generator import generate_frames
from rhombus_services.classifier import classify_directory
from rhombus_services.rhombus_finalizer import rhombus_finalizer
from rhombus_services.cleanup import cleanup
from rhombus_services.arg_parser import parse_arguments


class Main:
    """Entry point class, which handles all of the execution of requests and processing of object detection

    :attribute __api_key: The Api Key that is specified when running the application
    :attribute __camera_uuid: The Camera UUID that is specified when running the application
    :attribute __interval: The interval in seconds of fetching clips from the VOD, by default 10 second clips fetched every 10 seconds
    :attribute __connection_type: The ConnectionType that is specified when running the application
    :attribute __api_client: The RhombusAPI client that will be used throughout the lifetime of our application
    :attribute __http_client: The HTTP Client that will be used for fetching clips throughout the lifetime of our application
    :attribute __yolo_net: The YOLO classifier neural net that will be used throughout the lifetime of our application
    :attribute __coco_classes: All of the available COCO class names, viewable in yolo/coco.names
    """

    __api_key: str
    __api_client: rapi.ApiClient
    __connection_type: ConnectionType
    __camera_uuid: str
    __interval: int = 10
    __http_client: requests.sessions.Session
    __yolo_net: cv2.dnn_Net
    __coco_classes: List[str]

    def __init__(self, args: argparse.Namespace) -> None:
        """Constructor for the Main class, which will initialize all of the clients and arguments

        :param args: The parsed user cmd arguments
        """

        # Save the cmd args in our runner
        self.__camera_uuid = args.camera_uuid
        self.__interval = args.interval
        self.__api_key = args.api_key

        # Create an API Client and Configuration which will be used throughout the program
        config: rapi.Configuration = rapi.Configuration()
        config.api_key['x-auth-apikey'] = args.api_key

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

        # Create our neural net
        self.__yolo_net = cv2.dnn.readNetFromDarknet('yolo/yolov3.cfg', 'yolo/yolov3.weights')
        self.__yolo_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)

        # Load the classes from the coco.names file
        self.__coco_classes = open('yolo/coco.names').read().strip().split('\n')

    def __runner(self) -> None:
        """Executes the services that will download the clip, classify it, and upload the bounding boxes to Rhombus."""

        # Start a timer to time our execution time
        start = timer()

        print("Fetching URIs...")

        # Get the media URIs from rhombus for our camera, this is done every sequence so that we don't have to worry about federated tokens. 
        # These URIs stay the same, but this method will also create our federated tokens
        uri, token = fetch_media_uris(api_client=self.__api_client, camera_uuid=self.__camera_uuid, duration=120,
                                      connection_type=self.__connection_type)

        print("Downloading the VOD...")

        # Download the mp4 of the last [duration] seconds starting from Now - [duration] seconds ago
        clip_path, directory_path, start_time = fetch_vod(api_key=self.__api_key, federated_token=token,
                                                          http_client=self.__http_client, uri=uri,
                                                          connection_type=self.__connection_type,
                                                          duration=self.__interval)

        print("Generating frames...")

        # Generate a bunch of frames from our downloaded mp4, these will be put in vodRes.directoryPath/FRAME.jpg and the number of them will depend on the FPS, which is set right now to 3
        generate_frames(clip_path=clip_path, directory_path=directory_path, FPS=3.0)

        print("Classifying Images...")

        # Classify all of the frames generated in the vodRes.directoryPath
        boxes = classify_directory(self.__yolo_net, self.__coco_classes, directory_path, start_time, self.__interval)

        print("Sending the data to Rhombus...")

        # Send all of our bounding boxes to rhombus
        rhombus_finalizer(self.__api_client, self.__camera_uuid, boxes)

        print("Cleaning up!")

        # Remove the downloaded files, the mp4 and jpgs
        cleanup(directory_path)

        # End timer
        end = timer()

        # Get the total execution time
        total_time = end - start

        # If we are underneath our interval, then we will want to sleep. 
        # Otherwise if we are over our interval, then that means we are lagging behind and we need to process the next interval immediately
        if(total_time < self.__interval):
            # Sleep for remaining time
            time.sleep(self.__interval - total_time)

        # Run again
        self.__runner()

    def execute(self):
        """Starts the runner, which will create a scheduled loop of runners."""
        self.__runner()


if __name__ == "__main__":
    # Get the user's arguments
    args = parse_arguments(sys.argv[1:])

    # Start the main runner
    Main(args).execute()
