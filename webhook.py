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

import atexit
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import requests as requests
import urllib3
from flask import Flask
from flask import request
from flask_ngrok import _download_ngrok
import argparse
from threading import Timer

import rhombus_logging
from copy_footage_to_local_storage import get_segment_uri, get_segment_uri_index
from rhombus_mpd_info import RhombusMPDInfo

app = Flask(__name__)

API_URL = "https://api2.rhombussystems.com"
tunnel_url: str | None
sess: requests.session = requests.session()
output: str | None

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LOGGER = rhombus_logging.get_logger("rhombus.Webhook")


def init_arg_parser():
    parser = argparse.ArgumentParser(
        description='Registers a webhook with Rhombus')
    parser.add_argument('--api_key', '-a', type=str, required=True,
                        help='Rhombus API key')
    parser.add_argument('--output', '-o', type=str, required=True,
                        help='The output directory to write video clips')
    parser.add_argument('--debug', '-g', required=False, action='store_true',
                        help='Print debug logging')
    return parser


def rpost(path: str, payload=None, headers=None) -> requests.Response:
    return sess.post(API_URL + path, json=payload, headers=headers)


def init(cli_args):
    arg_parser = init_arg_parser()
    args = arg_parser.parse_args(cli_args)

    if args.debug:
        LOGGER.setLevel("DEBUG")

    sess.headers = {
        "x-auth-scheme": "api-token",
        "x-auth-apikey": args.api_key}

    sess.verify = False

    global output
    output = args.output

    os.makedirs(output, exist_ok=True)


def run():
    start_ngrok()
    print(tunnel_url)
    r = rpost("/api/integrations/updateWebhookIntegration",
              payload={
                  "webhookSettings": {
                      "enabled": True, "webhookUrl": tunnel_url
                  }
              })
    if r.status_code != 200:
        # TODO(Brandon): Add something here.
        pass


def start_ngrok():
    """
    Starts Ngrok. Ngrok is used to create a public URL which Rhombus can use for the Webhook
    by port forwarding localhost.
    Credit to: https://github.com/gstaff/flask-ngrok
    """
    ngrok_path = str(Path(tempfile.gettempdir(), "ngrok"))
    _download_ngrok(ngrok_path)
    system = platform.system()
    if system == "Darwin":
        command = "ngrok"
    elif system == "Windows":
        command = "ngrok.exe"
    elif system == "Linux":
        command = "ngrok"
    else:
        raise Exception(f"{system} is not supported")
    executable = str(Path(ngrok_path, command))
    os.chmod(executable, 777)

    ngrok = subprocess.Popen([executable, 'http', '5000'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    atexit.register(ngrok.terminate)
    localhost_url = "http://localhost:4040/api/tunnels"
    time.sleep(1)

    global tunnel_url
    tunnel_url = requests.get(localhost_url).text
    j = json.loads(tunnel_url)

    tunnel_url = j['tunnels'][0]['public_url']
    tunnel_url = tunnel_url.replace("https", "http")


@app.route("/", methods=['POST'])
def root():
    data = request.json
    print(data)

    device_uuid = data['deviceUuid']
    clip_location_map = data['clipLocationMap']
    location = clip_location_map[device_uuid]

    alert_uuid = data['alertUuid']
    duration_sec = int(data['durationSec'])
    summary = data['summary']

    mpd_uri = "https://media.rhombussystems.com/media/metadata/" + device_uuid + "/" + location + "/" + alert_uuid + "/clip.mpd"
    LOGGER.debug("MPD URI %s", mpd_uri)
    r = sess.get(mpd_uri)

    rhombus_mpd_info = RhombusMPDInfo(str(r.content, 'utf-8'))

    out = Path(output, summary + "_" + alert_uuid + ".mp4")

    with open(out, "wb") as output_fp:
        init_seg_uri = get_segment_uri(mpd_uri, rhombus_mpd_info.init_string)
        LOGGER.debug("Init segment uri: %s", init_seg_uri)

        r = sess.get(init_seg_uri)
        LOGGER.debug("seg_init_resp: %s", r)

        output_fp.write(r.content)
        output_fp.flush()

        for cur_seg in range(int(duration_sec / 2)):
            seg_uri = get_segment_uri_index(rhombus_mpd_info, mpd_uri,
                                            cur_seg)
            LOGGER.debug("Segment uri: %s", seg_uri)

            seg_resp = sess.get(seg_uri)
            LOGGER.debug("seg_resp: %s", seg_resp)

            output_fp.write(seg_resp.content)
            output_fp.flush()

        output_fp.close()

    return "success"


if __name__ == '__main__':
    init(sys.argv[1:])

    thread = Timer(1, run)
    thread.daemon = True
    thread.start()
    app.run()
