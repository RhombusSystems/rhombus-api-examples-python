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
from flask import Flask
from flask_ngrok import _download_ngrok
import argparse
from threading import Timer

app = Flask(__name__)

API_URL = "https://api2.rhombussystems.com"


def init_arg_parser():
    parser = argparse.ArgumentParser(
        description='Registers a webhook with Rhombus')
    parser.add_argument('--api_key', '-a', type=str, required=True,
                        help='Rhombus API key')
    parser.add_argument('--debug', '-g', required=False, action='store_true',
                        help='Print debug logging')
    return parser


def rpost(sess: requests.session, path: str, payload) -> requests.Response:
    return sess.post(API_URL + path, json=payload)


class RhombusWebhook:
    tunnel_url: str | None
    sess: requests.session

    def __init__(self, cli_args):
        arg_parser = init_arg_parser()
        args = arg_parser.parse_args(cli_args)

        self.tunnel_url = None
        self.sess = requests.session()

        self.sess.headers = {
            "x-auth-scheme": "api-token",
            "x-auth-apikey": args.api_key}

        self.sess.verify = False

    def start(self):
        self.start_ngrok()
        print(self.tunnel_url)
        r = rpost(self.sess, "/api/integrations/updateWebhookIntegration",
                  {"enabled": True})
        print(r.content)

    def start_ngrok(self):
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
        localhost_url = "http://localhost:4040/api/tunnels"  # Url with tunnel details
        time.sleep(1)
        self.tunnel_url = requests.get(localhost_url).text  # Get the tunnel information
        j = json.loads(self.tunnel_url)

        self.tunnel_url = j['tunnels'][0]['public_url']  # Do the parsing of the get
        self.tunnel_url = self.tunnel_url.replace("https", "http")


@app.route("/")
def hello():
    return "Hello"


if __name__ == '__main__':
    instance = RhombusWebhook(sys.argv[1:])

    thread = Timer(1, instance.start)
    thread.daemon = True
    thread.start()
    app.run()
