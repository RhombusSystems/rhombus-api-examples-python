# Rhombus Face Detection Module 

## What is this
Rhombus Face Detection Module is a Python commandline application that recognizes faces in Rhombus Systems cameras using the OpenCV to determine if someone is not in frame. This is an example of how to use the [Rhombus API](https://apidocs.rhombussystems.com/reference). This is NOT a production ready example, it is for demonstrational purposes only

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

3. Run `cd FaceDetectionModule`
4. Run the example using  `python3 main.py --api_key <YOUR_API_KEY> --camera_uuid <YOUR_CAMERA_UUID> --name <YOUR_REQUESTED_NAME> --`
