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

    # The --connection_type or -t param will hold the ConnectionType to the camera. It is not recommended to run in WAN mode unless this python server is running on a separate network from the camera
    parser.add_argument('--connection_type', '-t', type=str, required=False,
                        help='The connection type to the camera, either LAN or WAN (default LAN)', default="LAN")

    # Return all of our arguments
    return parser.parse_args(argv)
