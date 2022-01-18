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

# Import type hints
from threading import Lock
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

# Import webhook services
from rhombus_services.webhook import init_webhook, WebhookEvent

# Import our connection type
from helper_types.connection_type import ConnectionType

# Import some logging utilities
from logging_utils.colors import LogColors

# Import all of our services which will do the heavy lifting
from rhombus_services.media_uri_fetcher import fetch_media_uris, fetch_federated_token
from rhombus_services.vod_fetcher import fetch_vod, fetch_alert_vod
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
    :attribute __mutex: The mutex lock that controls the YOLO classifier to prevent it from being used at the same time by multiple webhook events.
    """

    __api_key: str
    __api_client: rapi.ApiClient
    __connection_type: ConnectionType
    __camera_uuid: str
    __interval: int = 10
    __http_client: requests.sessions.Session
    __yolo_net: cv2.dnn_Net
    __coco_classes: List[str]
    __should_poll: bool = False
    __mutex = Lock()

    def __init__(self, args: argparse.Namespace) -> None:
        """Constructor for the Main class, which will initialize all of the clients and arguments

        :param args: The parsed user cmd arguments
        """

        # Save the cmd args in our runner
        self.__api_key = args.api_key
        self.__should_poll = args.continuous

        if self.__should_poll:
            self.__camera_uuid = args.camera_uuid
            self.__interval = args.interval

            # By default the connection type is LAN, unless otherwise specified by the user
            self.__connection_type = ConnectionType.LAN

            # If the user specifies -t WAN, then we need to run in WAN mode, however this is not recommended
            if args.connection_type == "WAN":
                self.__connection_type = ConnectionType.WAN
                print(
                    LogColors.WARNING + "Running in WAN mode! This is not recommended if it can be avoided." + LogColors.ENDC)

        # Create an API Client and Configuration which will be used throughout the program
        config: rapi.Configuration = rapi.Configuration()
        config.api_key['x-auth-apikey'] = args.api_key

        # We need to set the additional header of x-auth-scheme, otherwise we will receive 401
        self.__api_client = rapi.ApiClient(configuration=config, header_name="x-auth-scheme", header_value="api-token")

        # Create an HTTP client
        self.__http_client = requests.sessions.Session()

        # Create our neural net
        self.__yolo_net = cv2.dnn.readNetFromDarknet('yolo/yolov3.cfg', 'yolo/yolov3.weights')
        self.__yolo_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)

        # Load the classes from the coco.names file
        self.__coco_classes = open('yolo/coco.names').read().strip().split('\n')

    def __parse_and_classify(self, clip_path: str, directory_path: str, start_time_sec: int, duration_sec: int,
                             device_uuid: str) -> None:
        """Classifies a directory containing a downloaded video clip and sends the bounding box data to Rhombus.

        :param clip_path: The path to the actual mp4 video clip that was downloaded.
        :param directory_path: The parent directory of the mp4 video clip where we can output things like frames and whatnot.
        :param start_time_sec: The start time in seconds since epoch.
        :param duration_sec: The duration of the video clip that was downloaded.
        :param device_uuid: The camera UUID that the clip was downloaded from.
        """

        print("Generating frames...")

        # Generate a bunch of frames from our downloaded mp4, these will be put in vodRes.directoryPath/FRAME.jpg and
        # the number of them will depend on the FPS, which is set right now to 3
        generate_frames(clip_path=clip_path, directory_path=directory_path, FPS=3.0)

        print("Classifying Images...")

        # Classify all of the frames generated in the vodRes.directoryPath
        boxes = classify_directory(self.__yolo_net, self.__coco_classes, directory_path, start_time_sec,
                                   duration_sec)

        print("Sending the data to Rhombus...")

        # Send all of our bounding boxes to rhombus
        rhombus_finalizer(self.__api_client, device_uuid, boxes)

    def __webhook_run(self, data: WebhookEvent) -> None:
        """Response to webhook events by downloading the associated video clip.

        :param data: The webhook event data.
        """
        print("Fetching federated token...")

        token = fetch_federated_token(api_client=self.__api_client)

        print("Downloading the VOD...")

        # Download the mp4 of the last [duration] seconds starting from Now - [duration] seconds ago
        clip_path, directory_path = fetch_alert_vod(api_key=self.__api_key, federated_token=token,
                                                    http_client=self.__http_client, uri=data.mpd_uri,
                                                    duration_sec=data.duration_sec, alert_uuid=data.alert_uuid)

        with self.__mutex:
            # Parse and classify the newly downloaded video clip.
            self.__parse_and_classify(clip_path, directory_path, int(data.timestamp_ms / 1000), data.duration_sec,
                                      data.device_uuid)

            print("Cleaning up!")

            # Remove the downloaded files, the mp4 and jpgs
            cleanup(directory_path)

    def __interval_runner(self) -> None:
        """Executes the services that will download the clip, classify it, and upload the bounding boxes to Rhombus."""

        # Check to make sure that the user put in the parameters properly before proceeding.
        if self.__camera_uuid is None:
            print(LogColors.ERROR + "No camera UUID has been specified. When running in poll mode, make sure "
                                    "you are using the --camera_uuid option to specify which camera to poll "
                                    "video clips from. Run this application with --help for more info.")
            return

        # Start a timer to time our execution time
        start = timer()

        print("Fetching URIs...")

        # Get the media URIs from rhombus for our camera, this is done every sequence so that we don't have to worry
        # about federated tokens. These URIs stay the same, but this method will also create our federated tokens
        uri, token = fetch_media_uris(api_client=self.__api_client, camera_uuid=self.__camera_uuid, duration=120,
                                      connection_type=self.__connection_type)

        print("Downloading the VOD...")

        # Download the mp4 of the last [duration] seconds starting from Now - [duration] seconds ago
        clip_path, directory_path, start_time_sec = fetch_vod(api_key=self.__api_key, federated_token=token,
                                                              http_client=self.__http_client, uri=uri,
                                                              connection_type=self.__connection_type,
                                                              duration=self.__interval)

        # Parse and classify the newly downloaded VOD.
        self.__parse_and_classify(clip_path, directory_path, start_time_sec, self.__interval, self.__camera_uuid)

        print("Cleaning up!")

        # Remove the downloaded files, the mp4 and jpgs
        cleanup(directory_path)

        # End timer
        end = timer()

        # Get the total execution time
        total_time = end - start

        # If we are underneath our interval, then we will want to sleep. Otherwise if we are over our interval,
        # then that means we are lagging behind and we need to process the next interval immediately
        if total_time < self.__interval:
            # Sleep for remaining time
            time.sleep(self.__interval - total_time)

        # Run again
        self.__interval_runner()

    def execute(self):
        """Starts the runner, which will create a scheduled loop of runners."""
        if self.__should_poll:
            self.__interval_runner()
        else:
            init_webhook(__name__, self.__api_client, self.__webhook_run)


if __name__ == "__main__":
    # Get the user's arguments
    args = parse_arguments(sys.argv[1:])

    # Start the main runner
    Main(args).execute()
