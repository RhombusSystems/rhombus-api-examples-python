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
from typing import List

import flask
import requests as requests
import urllib3 as urllib3

sys.path.append('../')

from rhombus_mpd_info import RhombusMPDInfo
import rhombus_logging

from flask import Flask
from flask import request

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LOGGER = rhombus_logging.get_logger("rhombus.LiveStreaming")

API_URL = "https://api2.rhombussystems.com"


def parse_arguments(argv: List[str]) -> argparse.Namespace:
    """Parse the command line args.

    :param argv: The Commandline arguments from the user, which can be retrieved via sys.argv[1:]
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


def get_segment_uri(mpd_uri, segment_name):
    if "file.mpd" in mpd_uri:
        return mpd_uri.replace("file.mpd", segment_name)
    elif "live.mpd" in mpd_uri:
        return mpd_uri.replace("live.mpd", segment_name)
    else:
        return None


def get_segment_uri_index(rhombus_mpd_info, mpd_uri, index):
    segment_name = rhombus_mpd_info.segment_pattern.replace("$Number$", str(index + rhombus_mpd_info.start_index))
    return get_segment_uri(mpd_uri, segment_name)


class Main:
    live_uri: str
    mpd_doc: str
    mpd_info: RhombusMPDInfo
    federated_token: str
    sess: requests.session = requests.session()
    app: Flask
    port: int

    def __init__(self, args: argparse.Namespace):
        self.sess.headers = {
            "x-auth-scheme": "api-token",
            "x-auth-apikey": args.api_key}

        self.sess.verify = False

        self.port = args.port

        LOGGER.debug("Getting media URIs")

        r = self.rpost("/api/camera/getMediaUris", payload={"cameraUuid": args.camera_uuid})

        if r.status_code != 200:
            LOGGER.error("Failed to get media URIs")
            return

        media_uris_response = r.json()

        self.live_uri = media_uris_response["lanLiveMpdUris"][0]

        try:
            LOGGER.debug("Trying LAN connection...")
            self.sess.get(self.live_uri)
            LOGGER.debug("LAN connection successful!")
        except:
            LOGGER.debug("LAN connection failed, falling back to WAN!")
            self.live_uri = media_uris_response["wanLiveMpdUri"]

        LOGGER.info("Using WAN live MPD URI %s", self.live_uri)

        LOGGER.debug("Fetching federated token...")
        r = self.rpost("/api/org/generateFederatedSessionToken", payload={"durationSec": 60 * 60})

        if r.status_code != 200:
            LOGGER.error("Failed to retrieve federated session token, cannot continue: %s", r.content)
            return

        self.federated_token = r.json()["federatedSessionToken"]

        LOGGER.debug("Getting MPD doc")

        r = self.sess.get(self.live_uri, headers=self.get_media_headers())

        if r.status_code != 200:
            LOGGER.error("Failed to get MPD doc")

        self.mpd_doc = str(r.content, 'utf-8')
        self.mpd_info = RhombusMPDInfo(self.mpd_doc)

        LOGGER.info("Using MPD doc %s", self.mpd_doc)

        self.app = Flask(__name__)

        @self.app.route("/")
        def send_webpage():
            return flask.render_template("index.html", g_URL=request.url_root + "live.mpd")

        @self.app.route("/live.mpd")
        def send_mpd():
            return flask.Response(self.mpd_doc, 200)

        @self.app.route("/" + self.mpd_info.init_string)
        def seg_init():
            LOGGER.debug("Getting initial segment!")
            response = self.sess.get(get_segment_uri(self.live_uri, self.mpd_info.init_string))

            if response.status_code != 200:
                LOGGER.error("Failed to get init segment!")
                return flask.Response(response.reason, response.status_code)

            return flask.Response(response.content, 200)

        @self.app.route("/" + self.mpd_info.segment_pattern.replace("$Number$", "<number>"))
        def seg_get(number: str):
            LOGGER.info("Getting segment %d", int(number))
            response = self.sess.get(get_segment_uri_index(self.mpd_info, self.live_uri, int(number)))

            if response.status_code != 200:
                LOGGER.error("Failed to get segment %d", int(number))
                return flask.Response(response.reason, response.status_code)

            return flask.Response(response.content, 200)

    def rpost(self, path: str, payload=None, headers=None) -> requests.Response:
        return self.sess.post(API_URL + path, json=payload, headers=headers)

    def get_media_headers(self) -> dict[str, str]:
        return {"Cookie": "RSESSIONID=RFT:" + str(self.federated_token)}

    def execute(self):
        self.app.run(port=self.port)


def init(argv) -> None:
    args = parse_arguments(argv)

    if args.debug:
        LOGGER.setLevel("DEBUG")

    Main(args).execute()


if __name__ == '__main__':
    init(sys.argv[1:])
