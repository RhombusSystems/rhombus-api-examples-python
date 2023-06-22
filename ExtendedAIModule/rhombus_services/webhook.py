import atexit
import json
import os
import platform
import subprocess
import tempfile
import time
from pathlib import Path
from threading import Timer

import requests
from flask import Flask, request
from flask_ngrok import _download_ngrok

import RhombusAPI as rapi
from typing import Callable


class WebhookEvent:
    """Contains data received from a webhook event to be used in webhook callbacks.

    :attribute device_uuid: The camera UUID that is related to this event.
    :attribute location: Which region this event came from.
    :attribute alert_uuid: The UUID associated for this alert.
    :attribute duration_sec: The duration in seconds that the clip lasts for this event.
    :attribute summary: The summary of this alert.
    :attribute timestamp_ms: The milliseconds since epoch that this alert appears.
    :attribute mpd_uri: The MPD URI that contains the video clip.
    """
    device_uuid: str
    location: str
    alert_uuid: str
    duration_sec: int
    summary: str
    timestamp_ms: int

    def __init__(self, data: any):
        """Constructor for a webhook event which parses the JSON response from Rhombus.

        :param data: The JSON data map for the Webhook event unparsed from Rhombus.
        """
        self.device_uuid = data['deviceUuid']
        clip_location_map = data['clipLocationMap']
        self.location = clip_location_map[self.device_uuid]

        self.alert_uuid = data['alertUuid']
        self.duration_sec = int(data['durationSec'])
        self.summary = data['summary']
        self.timestamp_ms = int(data['timestampMs'])

    @property
    def mpd_uri(self) -> str:
        """Gets the MPD URI associated with this webhook event."""
        return "https://media.rhombussystems.com/media/metadata/" + self.device_uuid + "/" + self.location + "/" + self.alert_uuid + "/clip.mpd"


def __start_ngrok() -> str:
    """
    Starts Ngrok. Ngrok is used to create a public URL which Rhombus can use for the Webhook
    by port forwarding localhost.
    Credit to: https://github.com/gstaff/flask-ngrok
    """

    # Gets a temporary place to put the Ngrok executable.
    ngrok_path = str(Path(tempfile.gettempdir(), "ngrok"))

    # Downloads Ngrok to this local directory.
    _download_ngrok(ngrok_path)

    # Gets the proper command to run depending on the operating system.
    system = platform.system()
    if system == "Darwin":
        command = "ngrok"
    elif system == "Windows":
        command = "ngrok.exe"
    elif system == "Linux":
        command = "ngrok"
    else:
        raise Exception(f"{system} is not supported")

    # Gets the executable location.
    executable = str(Path(ngrok_path, command))

    # Grants permission to the executable that Ngrok needs.
    os.chmod(executable, 777)

    # Opens a subprocess to run Ngrok. We don't want the output that Ngrok pipes to STDOUT, so we will just hide it.
    ngrok = subprocess.Popen([executable, 'http', '5000'], stdout=subprocess.DEVNULL)

    # Terminate the ngrok process when the application exits.
    atexit.register(ngrok.terminate)

    # This localhost URL will give information about the Ngrok connection.
    localhost_url = "http://localhost:4040/api/tunnels"

    # TODO(Brandon): This is a pretty big hack that seems to work pretty well, but shouldn't
    time.sleep(3)

    # Get the Ngrok tunnel information.
    tunnel_url = requests.get(localhost_url).text

    # Loads the information from the JSON URL
    j = json.loads(tunnel_url)

    # Gets the public URL.
    tunnel_url = j['tunnels'][0]['public_url']

    # Returns this URL.
    # TODO(Brandon): Figure out why this is occuring.
    return tunnel_url.replace("https", "http")


def __run(api_client: rapi.ApiClient) -> None:
    """
    Initializes the Webhook and sends the information to Rhombus.

    :param api_client: The Rhombus API client that can be used to make requests.
    """

    # Start Ngrok
    tunnel_url = __start_ngrok()

    # Get the API.
    api = rapi.IntegrationsWebserviceApi(api_client)

    # Make the request to Rhombus containing our webhook URL.
    body = rapi.IntegrationUpdateWebhookIntegrationWSRequest(
        webhook_settings=rapi.WebhookSettings(enabled=True, webhook_url=tunnel_url))

    # Get the response.
    response = api.update_webhook_integration(body=body)

    print("Rhombus responded with ")
    print(response)


def init_webhook(name: str, api_client: rapi.ApiClient, cb: Callable[[WebhookEvent], None]) -> None:
    """
    Initializes the webhook for Rhombus.

    :param name: The name of the flask application.
    :param api_client: The Rhombus API client.
    :param cb: The callback that will be called with the Webhook.
    """

    # Create the Flask app with the name.
    app = Flask(name)

    # Create a thread which will start Ngrok.
    thread = Timer(1, __run, [api_client])
    thread.daemon = True
    thread.start()

    # This method will handle POST requests to our Flask server.
    @app.route("/", methods=['POST'])
    def root():
        data = WebhookEvent(request.json)
        cb(data)
        return "success"

    # Start the Flask server.
    app.run(debug=True, use_reloader=False)
