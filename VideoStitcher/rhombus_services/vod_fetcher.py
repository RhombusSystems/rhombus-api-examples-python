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
from typing import Dict

# Import requests to download the VOD
import requests

# Import pathlib, OS, and IO to write the VOD to a file
import pathlib
import os
import io

# Import ConnectionType to specify what connection we should have to the camera when downloading our data
from rhombus_types.connection_type import ConnectionType


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


def fetch_vod(api_key: str, http_client: requests.sessions.Session, federated_token: str,  uri: str,
              connection_type: ConnectionType, dir: str, file_name: str, start_time: int, end_time: int) -> None:
    """Download a vod to disk. It will be saved in res/<current time in seconds>

    :param api_key: The API Key specified by the user
    :param http_client: The HTTP Client to download the files with which is initialized at startup
    :param federated_token: The federated token which will be used to download the files. Without this we would get a 401 authentication error
    :param uri: The VOD uri to download from
    :param connection_type: The ConnectionType to the Camera to download the VOD from
    :param dir: The directory where the output clip will be placed
    :param file_name: The name of the file to output
    :param start_time: The start timestamp in miliseconds in the VOD to start downloading at
    :param end_time: The end timestamp in miliseconds in the VOD to stop downloading at
    """
    duration = end_time - start_time + 1

    # We need to replace {START_TIME} and {DURATION} with the correct values in order to properly download the file
    full_uri = uri.replace("{START_TIME}", str(start_time)).replace("{DURATION}", str(duration))

    # If the directory does not already exist, then we need to create it
    if (not os.path.exists(dir)):
        pathlib.Path(dir).mkdir(parents=True, exist_ok=True)

    # The path of the clip is dir/clip.mp4 regardless of timestamp. The file is always called clip.mp4
    path = dir + file_name

    # These headers are necessary to download all of the VODs
    headers = {
        # The federated token is set as a cookie. Without this we would be unable to download the files from Rhombus
        "Cookie": "RSESSIONID=RFT:" + federated_token,

        # These headers below are necessary for almost all Rhombus requests, URL or API regardless
        "x-auth-apikey": api_key,
        "x-auth-scheme": "api-token",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    # This will change depend on whether we are using WAN or LAN
    mpd_name = "clip.mpd" if connection_type == ConnectionType.LAN else "file.mpd"

    # Create an output file. This will be written in bytes.
    with open(path, "wb") as file:
        # Because our URI is an mpd, we need to get each of the segments. The seg_init.mp4 is the first of these.
        # Just replace clip.mpd at the end of the URL with seg_init.mp4
        save_clip(headers, http_client, file, full_uri.replace(mpd_name, "seg_init.mp4"))

        # Each of the segments is 2 seconds long, so the number of segments is duration/2
        for i in range(int(duration / 2)):
            # The URI of all subsequent segments will replace clip.mpd with seg_<index>.m4v
            # These files will need to be appended to our existing clip.mp4 in disk
            save_clip(headers, http_client, file, full_uri.replace(mpd_name, "seg_" + str(i) + ".m4v"))

    # Close the output file
    file.close()
