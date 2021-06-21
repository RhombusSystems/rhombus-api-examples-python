# Rhombus Extended AI Module

## What is this
Rhombus Extended AI Module is a Python commandline application that identifies objects in Rhombus Systems cameras using the OpenCV and YOLO with the COCO model. This is an example of how to use the [Rhombus API](https://apidocs.rhombussystems.com/reference). This is NOT a production ready example, it is for demonstrational purposes only

The code demos how to send API requests to Rhombus using API token authentication and how to download VODs from Rhombus.


## Installation

### Generate RhombusAPI

NOTE: If you have already generated the Python client and have a RhombusAPI directory in the root source directory, then steps 1 and 2 are optional

1. Clone the repo with `git clone https://github.com/RhombusSystems/rhombus-api-examples-python.git` 
2. Run `curl https://raw.githubusercontent.com/RhombusSystems/rhombus-api-examples-codegen/main/python/install.sh | bash` in the root directory

### Download YOLO Weights and coco classes
3. Run `cd ExtendedAIModule`
4. Run `mkdir yolo`
5. Run `curl https://raw.githubusercontent.com/pjreddie/darknet/master/cfg/yolov3.cfg -o yolo/yolov3.cfg`
6. Run `curl https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names -o yolo/coco.names`
7. Run `curl https://pjreddie.com/media/files/yolov3.weights -o yolo/yolov3.weights`

### Running the demo

8. Run the example using `python3 main.py --api_key <YOUR_API_KEY> --camera_uuid <YOUR_CAMERA_UUID>`
