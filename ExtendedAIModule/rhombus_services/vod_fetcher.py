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
import sys
from typing import Dict
from typing import Tuple

# Import requests to download the VOD
import requests

# Import pathlib, OS, and IO to write the VOD to a file
import pathlib
import os
import io

# Import time to get the current time
import time

# Import ConnectionType to specify what connection we should have to the camera when downloading our data
from helper_types.connection_type import ConnectionType

from helper_types.rhombus_mpd_info import RhombusMPDInfo


def save_clip(headers: Dict[str, str], http_client: requests.sessions.Session, file: io.BufferedWriter,
              uri: str) -> None:
    """Save an m4v or mp4 url to the specified output file

    :param headers: The HTTP Headers to send with our request. These are required to authenticate
    :param http_client: The HTTP Client to download the files with which is initialized at startup
    :param file: The output file to write to
    :param uri: The media URI to download from
    """
    print("Saving clip " + uri)

    # Download the file from the uri
    buffer = http_client.get(uri, headers=headers)

    # Write the file
    file.write(buffer.content)

    # Flush our file and buffer
    file.flush()
    buffer.close()


# The possible MPD URI endings
URI_FILE_ENDINGS = ["clip.mpd", "file.mpd"]


def get_segment_uri(mpd_uri, segment_name) -> str:
    """Gets the URI of a segment with a given segment name.

    :param mpd_uri: The original MPD URI
    :param segment_name: The replacement name, for example "seg_init.mp4"
    :return: The new URI
    """
    for ending in URI_FILE_ENDINGS:
        if ending in mpd_uri:
            return mpd_uri.replace(ending, segment_name)

    return None


def get_segment_uri_index(rhombus_mpd_info, mpd_uri, index) -> str:
    """Gets the URI of a segment with a given index

    :param rhombus_mpd_info: The Rhombus MPD info
    :param mpd_uri: The original MPD URI
    :param index: The index starting from 0
    :return: The new URI
    """
    segment_name = rhombus_mpd_info.segment_pattern.replace("$Number$", str(index + rhombus_mpd_info.start_index))
    return get_segment_uri(mpd_uri, segment_name)


def fetch_alert_vod(api_key: str, federated_token: str, http_client: requests.sessions.Session, uri: str,
                    duration_sec: int, alert_uuid: str) -> Tuple[str, str]:
    """Downloads a vod to disk given a URI from a webhook alert.

    :param api_key: The API Key specified by the user
    :param federated_token: The federated token which will be used to download the files. Without this we would get a 401 authentication error
    :param http_client: The HTTP Client to download the files with which is initialized at startup
    :param uri: The VOD uri to download from
    :param duration_sec: The duration in seconds of the clip to download
    :param alert_uuid: The UUID of the alert that is being downloaded.
    :return: Returns the path of the downloaded vod mp4 and the directory in which that downloaded mp4 is in.
    """

    # The directory where we will place our clip is "<PROJECT_ROOT>/res/<alert_uuid>"
    dir = "./res/" + alert_uuid + "/"

    # If the directory does not already exist, then we need to create it
    if not os.path.exists(dir):
        pathlib.Path(dir).mkdir(parents=True, exist_ok=True)

    # The path of the clip is dir/clip.mp4
    path = dir + "clip.mp4"

    # These headers are necessary to download all of the VODs
    headers = {
        # The federated token is set as a cookie. Without this we would be unable to download the files from Rhombus
        "Cookie": "RSESSIONID=RFT:" + federated_token,

        # These headers below are necessary for almost all Rhombus requests, URI or API regardless
        "x-auth-apikey": api_key,
        "x-auth-scheme": "api-token",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    # Get the MPD info from the base URI.
    mpd_response = http_client.get(uri, headers=headers)

    # If the response failed, then there is nothing we can do
    if mpd_response.status_code != 200:
        raise ConnectionError()

    # Get the MPD info
    rhombus_mpd_info = RhombusMPDInfo(str(mpd_response.content, 'utf-8'))

    # Create an output file. This will be written in bytes.
    with open(path, "wb") as file:
        # Because our URI is an mpd, we need to get each of the segments. The seg_init.mp4 is the first of these.
        # Just replace clip.mpd at the end of the URL with seg_init.mp4
        save_clip(headers, http_client, file, get_segment_uri(uri, rhombus_mpd_info.init_string))

        # Each of the segments is 2 seconds long, so the number of segments is duration/2
        for i in range(int(duration_sec / 2)):
            # The URI of all subsequent segments will replace clip.mpd with seg_<index>.m4v
            # These files will need to be appended to our existing clip.mp4 in disk
            save_clip(headers, http_client, file, get_segment_uri_index(rhombus_mpd_info, uri, i))

        # Close the output file
        file.close()

    # Return our data
    return path, dir


def fetch_vod(api_key: str, federated_token: str, http_client: requests.sessions.Session, uri: str,
              connection_type: ConnectionType, duration: int = 20) -> Tuple[str, str, int]:
    """Download a vod to disk. It will be saved in res/<current time in seconds>

    :param api_key: The API Key specified by the user
    :param federated_token: The federated token which will be used to download the files. Without this we would get a 401 authentication error
    :param http_client: The HTTP Client to download the files with which is initialized at startup
    :param uri: The VOD uri to download from
    :param connection_type: The ConnectionType to the Camera to download the VOD from
    :param duration: The duration in seconds of the clip to download
    :return: Returns the path of the downloaded vod mp4 and the directory in which that downloaded mp4 is in.
             It will also return the timestamp in seconds since epoch of the startTime of the clip
    """
    # Get the starting time in seconds. This will be the current time in seconds since epoch - duration
    start_time = round(time.time()) - duration

    # We need to replace {START_TIME} and {DURATION} with the correct values in order to properly download the file
    full_uri = uri.replace("{START_TIME}", str(start_time)).replace("{DURATION}", str(duration))

    # The directory where we will place our clip is "<PROJECT_ROOT>/res/<startTime>"
    dir = "./res/" + str(start_time) + "/"

    # If the directory does not already exist, then we need to create it
    if not os.path.exists(dir):
        pathlib.Path(dir).mkdir(parents=True, exist_ok=True)

    # The path of the clip is dir/clip.mp4 regardless of timestamp. The file is always called clip.mp4
    path = dir + "clip.mp4"

    # These headers are necessary to download all of the VODs
    headers = {
        # The federated token is set as a cookie. Without this we would be unable to download the files from Rhombus
        "Cookie": "RSESSIONID=RFT:" + federated_token,

        # These headers below are necessary for almost all Rhombus requests, URI or API regardless
        "x-auth-apikey": api_key,
        "x-auth-scheme": "api-token",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    # Get the MPD info from the base URI.
    mpd_response = http_client.get(full_uri, headers=headers)

    # If the response failed, then there is nothing we can do
    if mpd_response.status_code != 200:
        raise ConnectionError()

    # Get the MPD info
    rhombus_mpd_info = RhombusMPDInfo(str(mpd_response.content, 'utf-8'))

    # Create an output file. This will be written in bytes.
    with open(path, "wb") as file:
        # Because our URI is an mpd, we need to get each of the segments. The seg_init.mp4 is the first of these.
        # Just replace clip.mpd at the end of the URL with seg_init.mp4
        save_clip(headers, http_client, file, get_segment_uri(full_uri, rhombus_mpd_info.init_string))

        # Each of the segments is 2 seconds long, so the number of segments is duration/2
        for i in range(int(duration / 2)):
            # The URI of all subsequent segments will replace clip.mpd with seg_<index>.m4v
            # These files will need to be appended to our existing clip.mp4 in disk
            save_clip(headers, http_client, file, get_segment_uri_index(rhombus_mpd_info, full_uri, i))

        # Close the output file
        file.close()

    # Return our data
    return path, dir, start_time
