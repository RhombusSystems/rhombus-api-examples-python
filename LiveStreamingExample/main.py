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
import argparse
import sys
import time
from typing import List

import flask
import requests as requests
import urllib3 as urllib3

sys.path.append('../')

from rhombus_mpd_info import RhombusMPDInfo
import rhombus_logging

from flask import Flask
from flask import request

# Disable warnings.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set up logging.
LOGGER = rhombus_logging.get_logger("rhombus.LiveStreaming")

# The base API URL.
API_URL = "https://api2.rhombussystems.com"

# Federated tokens will last 1 hour.
FEDERATED_TOKEN_DURATION_SEC = 60 * 60


def parse_arguments(argv: List[str]) -> argparse.Namespace:
    """Parse the command line args.

    :param argv: The Commandline arguments from the user, which can be retrieved via sys.argv[1:]
    :return: The parsed arguments.
    """

    # Create our parser
    parser = argparse.ArgumentParser(
        description='Creates a web-server that serves a Rhombus live stream to a webclient.')

    # The --api_key or -a param will hold our API key
    parser.add_argument('--api_key', '-a', type=str, required=True, help='Rhombus API key')

    # The --camera_uuid or -c param will hold the UUID of the camera which will be processed
    parser.add_argument('--camera_uuid', '-c', type=str, required=False,
                        help='Device Id to pull footage from. Required if continuous.')

    # The --debug or -d param will tell the program to print out debug information
    parser.add_argument('--debug', '-d', required=False, action='store_true',
                        help='Show debug information')

    # The --port or -p param will tell the program what port to use, by default it is 5000
    parser.add_argument('--port', '-p', type=int, required=False, help='Web-server port in localhost', default=5000)

    # Return all of our arguments
    return parser.parse_args(argv)


def get_segment_uri(mpd_uri: str, segment_name: str) -> str:
    """Returns the URI of a segment replacing the ending *.mpd string with the `segment_name`.
    For example: get_segment_uri(https://some_wan_uri/file.mpd, seg_init.mp4) -> https://some_wan_uri/seg_init.mp4

    Depending on if the connection is WAN or LAN, the ending will either be "file.mpd" or "live.mpd" respectively.
    This method will replace either type of connection.

    This method should really only be used to get the initial segment, to get a segment at a specific index, use
    `get_segment_uri_index`

    :param mpd_uri:      The live MPD URI to get the segment string for.
    :param segment_name: The name of the segment.
    :return: The segment URI.
    """

    if "file.mpd" in mpd_uri:
        # If the MPD URI is a WAN connection, it will end in "file.mpd"
        return mpd_uri.replace("file.mpd", segment_name)
    elif "live.mpd" in mpd_uri:
        # If the MPD URI is a LAN connection, it will end in "live.mpd"
        return mpd_uri.replace("live.mpd", segment_name)
    else:
        raise Exception("The mpd_uri {} does not contain a valid ending!".format(mpd_uri))


def get_segment_uri_index(rhombus_mpd_info: RhombusMPDInfo, mpd_uri: str, index: int) -> str:
    """Returns the URI of a segment replacing the ending *.mpd string with the proper segment number adhering to the `rhombus_mpd_info`.
    For example: get_segment_uri(some_rhombus_mpd_info, https://some_wan_uri/file.mpd, 200) -> https://some_wan_uri/seg_200.mp4
    assuming that `some_rhombus_mpd_info.

    :param rhombus_mpd_info: The parsed MPD document from `mpd_uri`.
    :param mpd_uri:          The live MPD URI to get the segment string for.
    :param index:            The segment index starting at 0.
                             NOTE: This function already adds the starting index so always start at 0
    :return: The segment URI.
    """

    # Get the segment name by replacing the $Number$ pattern with the index.
    segment_name = rhombus_mpd_info.segment_pattern.replace("$Number$", str(index + rhombus_mpd_info.start_index))

    # Then get the segment URI.
    return get_segment_uri(mpd_uri, segment_name)


class Main:
    """Main entry point of the program.

    :attribute federated_token:      The federated token used to make GET requests to the live URI.
    :attribute last_token_fetch_sec: The last time in seconds since epoch that the federated token was fetched.
    :attribute sess:                 The requests session containing the API key headers to make HTTP requests.
    :attribute app:                  The Flask server app.
    :attribute port:                 The port that the Flask server is hosted on.
    """
    # live_uri: str
    # mpd_doc: str
    # mpd_info: RhombusMPDInfo
    federated_token: str
    last_token_fetch_sec: int = 0
    sess: requests.session = requests.session()
    app: Flask
    port: int
    is_wan = False

    def __init__(self, args: argparse.Namespace):
        """Initialize the main entry point.

        :param args: The parsed arguments.
        """
        # Set the API key headers.
        self.sess.headers = {
            "x-auth-scheme": "api-token",
            "x-auth-apikey": args.api_key,
        }
        self.sess.verify = False

        # Set our port.
        self.port = args.port

        # Get the federated token
        self.fetch_federated_token()

        LOGGER.debug("Getting media URIs")

        # Get the media URIs
        r = self.rhombus_post("/api/camera/getMediaUris", payload={"cameraUuid": args.camera_uuid})

        # If this failed, then we need to fail early.
        if r.status_code != 200:
            raise Exception("Failed to get media URIs: {}".format(r.status_code))

        # Get the media URIs response JSON.
        media_uris_response = r.json()

        # Set our live URI to the LAN URI by default.
        live_uri = media_uris_response["lanLiveMpdUris"][0]

        try:
            # Try the LAN connection
            LOGGER.debug("Trying LAN connection...")
            r = self.sess.get(live_uri)

            # If we successfully reach here, that means that the LAN connection works.
            LOGGER.debug("LAN connection successful!")
        except:
            # If an exception occurs, then that likely means we will need a WAN connection so fall back.
            LOGGER.debug("LAN connection failed, falling back to WAN!")
            live_uri = media_uris_response["wanLiveMpdUri"]
            self.is_wan = True

        LOGGER.info("Using live MPD URI %s", live_uri)

        # Fetch the MPD document.
        LOGGER.debug("Getting MPD doc")

        # The MPD document can be retrieved just by GETting the live URI.
        r = self.sess.get(live_uri, headers=self.get_media_headers())

        # If there was an error we need to fail early.
        if r.status_code != 200:
            raise Exception("Failed to get MPD doc: {}".format(r.status_code))

        # Get the actual MPD document string.
        mpd_doc = str(r.content, 'utf-8')

        # Parse the raw MPD document string.
        mpd_info = RhombusMPDInfo(mpd_doc)

        LOGGER.info("Using MPD doc %s", mpd_doc)

        # Create the flask app.
        self.app = Flask(__name__)

        # The / route will just serve the static HTML files.
        @self.app.route("/")
        def send_webpage():
            # We want to render "index.html" but we also want to use variable "g_URL" to tell the client where it can
            # get the live MPEG-DASH stream we are re-serving with this server.
            return flask.render_template("index.html", g_URL=request.url_root + "live.mpd")

        # The /live.mpd route will serve the MPD document that we already retrieved from Rhombus.
        @self.app.route("/live.mpd")
        def send_mpd():
            return flask.Response(mpd_doc, 200)

        # Using the parsed MPD document we can figure out what the init string is, and we will create a path for it
        # so that we can forward the initial segment. This init_string is, for now, always "seg_init.mp4" so the
        # route will be "/seg_init.mp4" but this should not be hard-coded in case this gets updated in the future.
        # Instead, this information can be found in the MPD document.
        @self.app.route("/" + mpd_info.init_string)
        def seg_init():
            # Update the federated token if necessary
            self.fetch_federated_token()

            LOGGER.debug("Getting initial segment!")
            # Get the init segment.
            response = self.sess.get(get_segment_uri(live_uri, mpd_info.init_string), headers=self.get_media_headers())

            # If there was an error, then forward that onto the client.
            if response.status_code != 200:
                LOGGER.error("Failed to get init segment: %s", response.reason)
                return flask.Response(response.reason, response.status_code)

            # Otherwise, just forward those bytes to the client.
            return flask.Response(response.content, 200)

        # Using the parsed MPD document we can figure out what the segment path is, and we will create it, replacing
        # "$Number$" with the flask-friendly "<number>" to make it a variable. The client will then make a request to
        # the route "/seg_<number>.mp4", but again this should not be hard-coded in case it gets updated in the future.
        @self.app.route("/" + mpd_info.segment_pattern.replace("$Number$", "<number>"))
        def seg_get(number: str):
            # Update the federated token if necessary
            self.fetch_federated_token()

            # Get the segment index.
            # NOTE: For demonstration purposes, we are removing the start index then adding it back because the dash.js
            # client will automatically add the start_index as any MPEG-Dash client should.

            # Technically, you can and should just ignore the start_index, but it is something to keep in mind in case
            # your MPEG-Dash client does not automatically add this start_index.
            segment_index = int(number) - mpd_info.start_index

            LOGGER.info("Getting segment %d", segment_index)

            # Get the segment.
            response = self.sess.get(get_segment_uri_index(mpd_info, live_uri, segment_index),
                                     headers=self.get_media_headers())

            # If there was an error, then forward that onto the client.
            if response.status_code != 200:
                LOGGER.error("Failed to get segment %d: %s", segment_index, response.reason)
                return flask.Response(response.reason, response.status_code)

            # Otherwise, just forward those bytes to the client.
            return flask.Response(response.content, 200)

    def rhombus_post(self, path: str, payload=None, headers=None) -> requests.Response:
        """Make a POST API request to Rhombus.

        :param path: The API endpoint path.
        :param payload: The JSON payload.
        :param headers: Any headers, if any, in addition to the base API headers which are added by default.
        :return: The response
        """
        return self.sess.post(API_URL + path, json=payload, headers=headers)

    def fetch_federated_token(self) -> None:
        """Fetch a new federated token if necessary."""
        # Get the current seconds since epoch.
        current_sec = int(time.time())

        # If the last token fetch plus the token duration minus two minutes of buffer is greater than the current 
        # seconds since epoch, then we can assume that the federated token is still valid.
        if self.last_token_fetch_sec + FEDERATED_TOKEN_DURATION_SEC - 120 > current_sec:
            return

        LOGGER.info("Fetching federated token...")

        # Request a federated token.
        r = self.rhombus_post("/api/org/generateFederatedSessionToken",
                              payload={"durationSec": FEDERATED_TOKEN_DURATION_SEC})

        # If something went wrong, then we need to fail early.
        if r.status_code != 200:
            raise Exception("Failed to retrieve federated session token, cannot continue: {}".format(r.status_code))

        # Update our federated token.
        self.federated_token = r.json()["federatedSessionToken"]
        # Update our last token fetch.
        self.last_token_fetch_sec = current_sec
        LOGGER.info("Received new federated token!")

    def get_media_headers(self) -> dict[str, str]:
        """Get the headers that need to be attached to a media URI request to include the federated token.

        :return: The header dictionary
        """
        return {"Cookie": "RSESSIONID=RFT:" + self.federated_token}

    def execute(self) -> None:
        """Run the flask web-server."""
        self.app.run(port=self.port)


def init(argv: List[str]) -> None:
    """Start the web-server.

    :param argv: The list of arguments specified by the user.
    """
    # Parse all of the arguments.
    args = parse_arguments(argv)

    # Set the debug level.
    if args.debug:
        LOGGER.setLevel("DEBUG")

    # Start the server.
    Main(args).execute()


if __name__ == '__main__':
    init(sys.argv[1:])
