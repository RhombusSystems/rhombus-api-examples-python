import RhombusAPI as rapi
import math as math
import io
import os
import pathlib
import requests

from rhombus_types.events import FinalizedEvent
from rhombus_services.vod_fetcher import fetch_vod
from rhombus_services.media_uri_fetcher import fetch_media_uris

from rhombus_types.connection_type import ConnectionType

# Import Subprocess to execute the ffmpeg command
import subprocess

def download_finalized_event_recursive(api_key: str, http_client: requests.sessions.Session, api_client: rapi.ApiClient, type: ConnectionType, event: FinalizedEvent, dir: str, vidlist: io.TextIOBase, index: int = 0) -> None:
    """Downloads finalized events

    :param api_key: The API key for sending requests to Rhombus
    :param http_client: The HTTP Client to download the files with which is initialized at startup
    :param api_client: The API Client for sending requests to Rhombus
    :param type: Whether to use LAN or WAN for the connection, by default LAN and unless you are on a different connection, you should really just use LAN
    :param event: The event to download the VOD from
    :param dir: The directory to output the VOD
    :param vidlist: The list of videos write buffer
    :param index: The recursive download index. When this function calls itself it will increase this value, you shouldn't really ever set this manually when calling the function.
    """

    # We are going to get our start time in seconds (thus divided by 1000) and then we will add a bit of padding to make sure we really download the full clip.
    # If the index is 0 (meaning our first clip) we will add a larger padding than the rest because oftentimes the exit event might not include some of the earlier events
    start_time = math.floor(event.start_time / 1000 - (4000 / 1000 if index == 0 else 1500 / 1000))

    # For the end time we will do the same thing. The end time has padding as well.
    end_time = math.ceil(event.end_time / 1000 + (4000 / 1000 if event.following_event == None else 1500 / 1000))

    # Get the camera UUID
    cam_uuid = event.data[0].camera.uuid

    # Fetch the media URIs using our type
    uri, federated_token = fetch_media_uris(api_client, cam_uuid, 60, type)
    
    # Download the VOD. It will be stored in a file "<dir>/<index>.mp4"
    fetch_vod(api_key, http_client, federated_token, uri, type, dir, str(index) + ".mp4", start_time, end_time)

    # The mp4 VOD that we download will need to be added to the vidlist.txt
    data = "file ''" + str(index) + ".mp4'\n";
    
    # Write to the vidlist
    vidlist.write(data);

    if event.following_event != None:
        # We will increase our index by 1 when calling this method and pass in our event.followingEvent as the event
        return download_finalized_event_recursive(api_key, http_client, api_client, type, event.following_event, dir, vidlist, index + 1)



def clip_combiner_pipeline(api_key: str, http_client: requests.sessions.Session, api_client: rapi.ApiClient, type: ConnectionType, event: FinalizedEvent, retry_index: int = 0) -> None:
    """Downloads a finalized event chain and then combines the downloaded clips into one stitched video

    :param api_key: The API key for sending requests to Rhombus
    :param http_client: The HTTP Client to download the files with which is initialized at startup
    :param api_client: The API Client for sending requests to Rhombus
    :param type: Whether to use LAN or WAN for the connection, by default LAN and unless you are on a different connection, you should really just use LAN
    :param event: The event to download the VOD from
    :param retry_index: The number of times retried to download
    """

    # The output directory will be "res/<start_time_in_miliseconds/"
    dir = "res/" + str(event.start_time) + "/"

    # If the directory already exists, then we shouldn't download it again
    if os.path.exists(dir):
        print("Already downloaded this clip, not downloading again!")
        return

    # Make the directory (since we already check to make sure it doesn't already exist, we can just do this)
    pathlib.Path(dir).mkdir(parents=True, exist_ok=True)

    # Open the vidlist file so that we can write to it
    with open(dir + "vidlist.txt", "w") as vidlist:

        # Download the VOD
        download_finalized_event_recursive(api_key=api_key, http_client=http_client, api_client=api_client, type=type, event=event, dir=dir, vidlist=vidlist)

        # Close the vidlist file since we are done with it now
        vidlist.close()

    # Run the FFMpeg command to combine the downloaded mp4s based on the vidlist.txt
    subprocess.run(["ffmpeg", "-f", "concat", "-safe", "0", "-i", dir + "vidlist.txt", "-c", "copy", dir+ "output.mp4"])

    print("Output stitched video in directory " + dir)
