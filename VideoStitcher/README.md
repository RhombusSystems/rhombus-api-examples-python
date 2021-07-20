# Rhombus VideoStitcher

## What is this
Rhombus VideoStitcher is a Python commandline application that attempts to automatically stitch together different video clips to follow someone around seemlessly. This is an example of how to use the [Rhombus API](https://apidocs.rhombussystems.com/reference). This is NOT a production ready example, it is for demonstrational purposes only

The code demos how to send API requests to Rhombus using API token authentication and how to download VODs from Rhombus.

## Requirements

### FFmpeg

[FFmpeg](https://ffmpeg.org/download.html) is required to download the mp4 videos and process the frames into jpegs which will be processed by the AI. Make sure you can run `ffmpeg` in the terminal and that it is working, otherwise this example will not work. If you have downloaded ffmpeg and it still isn't working in the terminal, make sure you add the path of your ffmpeg installation to the terminal rc file


## Installation

### Generate RhombusAPI

NOTE: If you have already generated the Python client and have a RhombusAPI directory in the root source directory, then steps 1 and 2 are optional

1. Clone the repo with `git clone https://github.com/RhombusSystems/rhombus-api-examples-python.git` 
2. Run `curl https://raw.githubusercontent.com/RhombusSystems/rhombus-api-examples-codegen/main/python/install.sh | bash` in the root directory


### Running the demo

3. Run `cd VideoStitcher`
4. Install the required packages through `pip3 install -r requirements.txt`
5. Create a `.env` file in the VideoStitcher source directory using the following structure (without the angle brackets)

    API_KEY=<YOUR API KEY>

    CONNECTION_TYPE=<WAN OR LAN> 

NOTE: CONNECTION_TYPE parameter is optional, but it will specify whether to use a WAN or LAN connection from the camera to download the VODs. It is by default LAN and unless the NodeJS server is running on a separate wifi from the camera, which would be very unlikely...

There are also many other environment variables that can be set, see `rhombus_environment/environment.py` for more information.

6. Run the example using `python3 main.py`
