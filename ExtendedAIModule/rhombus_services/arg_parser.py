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

# Import type hints
from typing import List

# Import argparse to parse our arguments for us easily
import argparse


def parse_arguments(argv: List[str]) -> argparse.Namespace:
    """Parse the command line args.
    
    :param argv: The Commandline arguments from the user, which can be retrieved via sys.argv[1:]
    """

    # Create our parser
    parser = argparse.ArgumentParser(description='Pulls footage from a camera on LAN and stores it to the filesystem.')

    # The --api_key or -a param will hold our API key
    parser.add_argument('--api_key', '-a', type=str, required=True, help='Rhombus API key')

    # The --camera_uuid or -c param will hold the UUID of the camera which will be processed
    parser.add_argument('--camera_uuid', '-c', type=str, required=True, help='Device Id to pull footage from')

    # The --interval or -i param will hold how often to poll the camera for new footage in seconds, by default 10 seconds
    parser.add_argument('--interval', '-i', type=int, required=False,
                        help='How often to poll the camera for new footage in seconds, by default 10 seconds',
                        default=10)

    # The --connection_type or -t param will hold the ConnectionType to the camera. It is not recommended to run in WAN mode unless this python server is running on a separate network from the camera
    parser.add_argument('--connection_type', '-t', type=str, required=False,
                        help='The connection type to the camera, either LAN or WAN (default LAN)', default="LAN")

    # Return all of our arguments
    return parser.parse_args(argv)
