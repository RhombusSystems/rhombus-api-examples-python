# Import sys and argparse for cmd args
import sys;
import argparse;

# Import requests to create our http client
import requests;

# Import threading to create infinitely running runner loop
import threading;

# Import OS to create our resource directory
import os;

sys.path.append('../')

# Import RhombusAPI to create our Api Client
import RhombusAPI as rapi;

# Import our connection type
from helper_types.connection_type import ConnectionType;

# Import some logging utilities
from logging_utils.colors import LogColors;

# Import all of our services which will do the heavy lifting
from rhombus_services.download_faces import download_faces;
from rhombus_services.cleanup import cleanup;
from rhombus_services.media_uri_fetcher import fetch_media_uris;
from rhombus_services.vod_fetcher import fetch_vod;
from rhombus_services.frame_generator import generate_frames;
from rhombus_services.arg_parser import parse_arguments;
from rhombus_services.encoding_generator import generate_encodings;
from rhombus_services.face_recognizer import recognize_faces_in_directory;


class Main:
    """Entry point class, which handles all of the execution of requests and processing of object detection

    :attribute __api_key: The Api Key that is specified when running the application
    :attribute __camera_uuid: The Camera UUID that is specified when running the application
    :attribute __interval: The interval in seconds of fetching clips from the VOD, by default 10 second clips fetched every 10 seconds
    :attribute __connection_type: The ConnectionType that is specified when running the application
    :attribute __force: The user specified option whether or not to force regeneration of the res/face_enc file ignoring whether it already exists or not. By default this is false.
    :attribute __name: The user specified name to look for in VODs.
    :attribute __api_client: The RhombusAPI client that will be used throughout the lifetime of our application
    :attribute __http_client: The HTTP Client that will be used for fetching clips throughout the lifetime of our application
    :attribute __counter: The number of times a user was not found in video footage.
    """

    __api_key: str;
    __api_client: rapi.ApiClient;
    __connection_type: ConnectionType;
    __camera_uuid: str;
    __interval: int = 10;
    __http_client: requests.sessions.Session;
    __force: bool = False;
    __name: str;
    __counter: int = 0;


    def __init__(self, args: argparse.Namespace) -> None:
        """Constructor for the Main class, which will initialize all of the clients and arguments

        :param args: The parsed user cmd arguments
        """

        # Save the cmd args in our runner
        self.__camera_uuid = args.camera_uuid;
        self.__interval = args.interval
        self.__api_key = args.api_key;
        self.__force = args.force;
        self.__name = args.name;

        # Create an API Client and Configuration which will be used throughout the program
        config: rapi.Configuration = rapi.Configuration();
        config.api_key['x-auth-apikey'] = args.api_key;

        # We need to set the additional header of x-auth-scheme, otherwise we will receive 401
        self.__api_client = rapi.ApiClient(configuration=config, header_name="x-auth-scheme", header_value="api-token");

        # By default the connection type is LAN, unless otherwise specified by the user
        self.__connection_type = ConnectionType.LAN;

        # If the user specifies -t WAN, then we need to run in WAN mode, however this is not recommended
        if(args.connection_type == "WAN"):
            self.__connection_type = ConnectionType.WAN
            print(LogColors.WARNING + "Running in WAN mode! This is not recommended if it can be avoided." + LogColors.ENDC)

        # Create an HTTP client
        self.__http_client = requests.sessions.Session();


    def __runner(self) -> None:
        """Executes the services that will download the clip, classify it, and upload the bounding boxes to Rhombus."""

        self.__schedule();
        
        # Get the media URIs from rhombus for our camera, this is done every sequence so that we don't have to worry about federated tokens. 
	    # These URIs stay the same, but this method will also create our federated tokens
        uri, token = fetch_media_uris(api_client=self.__api_client, camera_uuid=self.__camera_uuid, duration=120, type=self.__connection_type);

        # Download the mp4 of the last [duration] seconds starting from Now - [duration] seconds ago
        clip_path, directory_path, _ = fetch_vod(api_key=self.__api_key,  federated_token=token, http_client=self.__http_client, uri=uri, type=self.__connection_type, duration=self.__interval);

        # Generate a bunch of frames from our downloaded mp4, these will be put in vodRes.directoryPath/FRAME.jpg and the number of them will depend on the FPS, which is set right now to 3
        generate_frames(clip_path=clip_path, directory_path=directory_path, FPS=0.5);

        # Recognize all of the faces in our directory path which has all of our frames
        names: set[str] = recognize_faces_in_directory(directory=directory_path);

        # If our requested name is not found in our directory
        if(self.__name not in names):
            # Increase our counter by one
            self.__counter += 1;

            # Print out
            print("Get back to work " + self.__name + "!!!!");
            print(self.__name + " has not been at work " + str(self.__counter) + " times.");
        else:
            # Print out
            print("Hard at work");
        
        # Clean the clip in our resource directory
        cleanup(directory=directory_path);



    def execute(self):
        """Starts the runner, which will create a scheduled loop of runners."""

        # The resource directory will be in the root source directory / FaceDetectionModule / res
        res_dir: str = "./res";

        # If the resource directory doesn't exist, then create it
        if(not os.path.exists(res_dir)):
            os.mkdir(res_dir);

        print("Downloading faces... This can take anywhere from a couple of seconds to minutes to hours if there are many faces");

        # Get all of the faces identified through Rhombus and download thumbnails for them
        names = download_faces(api_key=self.__api_key, api_client=self.__api_client, http_client=self.__http_client);

        # Generate the encodings for our faces
        generate_encodings(names=names, force=self.__force);

        # Run the main recognizer
        self.__runner();

    def __schedule(self):
        """Schedule another runner."""

        # Each runner instance will run in a scheduled thread
        threading.Timer(args.interval, self.__runner).start();


if __name__ == "__main__":
    # Get the user's arguments
    args = parse_arguments(sys.argv[1:]);

    # Start the main runner
    Main(args).execute();
