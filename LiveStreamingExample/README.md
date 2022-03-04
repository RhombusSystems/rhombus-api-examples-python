# Rhombus Live Streaming Example

## What is this

Rhombus Live Streaming Example is a Python commandline application that re-streams a live Rhombus Systems camera feed to
a web client.

The code demos how to send API requests to Rhombus using API token authentication and how to forward MPEG-Dash segments
to a client.

## Installation

1. Run `cd LiveStreamingExample`
2. Run `pip3 install -r requirements.txt`

### Running the demo

3. Run the example using `python3 main.py --api_key <YOUR_API_KEY> --camera_uuid <YOUR_CAMERA_UUID>`
4. Open `http://localhost:5000`
