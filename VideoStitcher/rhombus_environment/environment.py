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

from dotenv import load_dotenv
import os
from rhombus_utils.singleton import Singleton

@Singleton
class Environment:
    """Environment class holds information from the `.env` file in the VideoStitcher directory

    :attribute api_key: The API key used to send RhombusAPI requests
    :attribute connection_type: The connection type to the camera used to download VODs
    :attribute edge_event_detection_distance_from_edge: The distance from the edge that should be considered for edge events from 0-1
    :attribute suggested_human_event_seconds_since_current_time: How long before the current time should the prompter suggest human events
    :attribute minimum_event_length: The minimum number of human events to even consider it a full exit or enter event
    :attribute capture_radius_meters: The capture radius when isolating cameras based on velocity of a person and camera location in meters
    :attribute exit_event_detection_duration_seconds: How long from the starting time to look for exit events in seconds
    :attribute exit_event_detection_offset_seconds: How long before the start time should the exit event detector start looking. It is recommended that this be greater than 0 so that events don't accidentally get missed
    :attribute related_event_detection_duration_seconds: How long from the end of a one exit event should the related event detector look for other events
    :attribute pixels_per_meter: The density of pixels to render per meter when rasterizing the cameras. A higher value will require more rasterization and thus processing power but will be more accurate. 
                                 However this doesn't really matter so it is recommended that this value be pretty low because the accuracy really doesn't matter.
    :attribute clip_combination_edge_padding_miliseconds: How much time in miliseconds should be added before the start of the first exit event when combining clips. This will allow some padding time. 
                                                          For example if the padding is 4 seconds, then 4 seconds of footage before the detected exit event should be added.
                                                          This is important in case someone might be like walking around in place before he leaves the camera's view, this might not be caught without the padding.
    :attribute clip_combination_padding_miliseconds: How much padding between each camera switch should be added in miliseconds.
    """
    api_key: str
    connection_type: str
    edge_event_detection_distance_from_edge: float
    suggested_human_event_seconds_since_current_time: int
    minimum_event_length: int
    capture_radius_meters: int
    exit_event_detection_duration_seconds: int
    exit_event_detection_offset_seconds: int
    related_event_detection_duration_seconds: int
    pixels_per_meter: int
    clip_combination_edge_padding_miliseconds: int
    clip_combination_padding_miliseconds: int

    def __init__(self):
        """Constructor for environment"""

        # Load our environment
        load_dotenv()

        self.api_key = str(os.getenv('API_KEY'))
        self.connection_type = str(os.getenv('CONNECTION_TYPE'))
        self.edge_event_detection_distance_from_edge = float(os.getenv('EDGE_EVENT_DETECTION_DISTANCE_FROM_EDGE') or 0.4)
        self.suggested_human_event_seconds_since_current_time = int(os.getenv('SUGGESTED_HUMAN_EVENT_SECONDS_SINCE_CURRENT_TIME') or 600)
        self.minimum_event_length = int(os.getenv('MINIMUM_EVENT_LENGTH') or 2)
        self.capture_radius_meters = int(os.getenv('CAPTURE_RADIUS_METERS') or 300)
        self.exit_event_detection_duration_seconds = int(os.getenv('EXIT_EVENT_DETECTION_DURATION_SECONDS') or 10 * 60)
        self.exit_event_detection_offset_seconds = int(os.getenv('EXIT_EVENT_DETECTION_OFFSET_SECONDS') or 0.5 * 60)
        self.related_event_detection_duration_seconds = int(os.getenv('RELATED_EVENT_DETECTION_DURATION_SECONDS') or 30)
        self.pixels_per_meter = int(os.getenv('PIXELS_PER_METER') or 3)
        self.clip_combination_edge_padding_miliseconds = int(os.getenv('CLIP_COMBINATION_EDGE_PADDING_MILISECONDS') or 4000)
        self.clip_combination_padding_miliseconds = int(os.getenv('CLIP_COMBINATION_PADDING_MILISECONDS ') or 1500)

