import requests
import argparse
import sys
import rhombus_logging
from datetime import datetime, timedelta
import urllib3

# just to prevent unnecessary logging since we are not verifying the host
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_logger = rhombus_logging.get_logger("rhombus.GetFrame")


class GetFrame:
    def __init__(self, cli_args):
        arg_parser = self.__initialize_argument_parser()
        self.args = arg_parser.parse_args(cli_args)

        if self.args.debug:
            _logger.setLevel("DEBUG")

        self.api_url = "https://api2.rhombussystems.com"

        if self.args.timestamp_ms:
            self.timestamp_ms = self.args.timestamp_ms
        else:
            now = datetime.now()
            self.timestamp_ms = int((now - timedelta(minutes=5)).timestamp() * 1000)

        # initialize api http client
        self.api_sess = requests.session()

        # auth scheme changes depending on whether using cert/key or just api token
        if self.args.cert and self.args.private_key:
            scheme = "api"
            self.api_sess.cert = (self.args.cert, self.args.private_key)
        else:
            scheme = "api-token"

        self.api_sess.headers = {
            "x-auth-scheme": scheme,
            "x-auth-apikey": self.args.api_key}

        self.api_sess.verify = False

    def execute(self):
        frame_uri_request = {
            "cameraUuid": self.args.device_id,
            "timestampMs": self.timestamp_ms,
            "permyriadCropX": self.args.permyriad_x,
            "permyriadCropY": self.args.permyriad_y,
            "permyriadCropWidth": self.args.permyriad_width,
            "permyriadCropHeight": self.args.permyriad_height,
            "downscaleFactor": self.args.downscale,
            "jpgQuality": self.args.quality
        }

        _logger.debug("frame uri request: %s", frame_uri_request)

        frame_uri_resp = self.api_sess.post(self.api_url + "/api/video/getExactFrameUri", json=frame_uri_request)

        _logger.debug("Federated session token response: %s", frame_uri_resp.content)

        if frame_uri_resp.status_code != 200:
            _logger.warn("Failed to retrieve frame uri, cannot continue: %s", frame_uri_resp.content)
            return

        frame_uri = frame_uri_resp.json()["frameUri"]
        _logger.debug("Using frame uri: %s", frame_uri)
        frame_uri_resp.close()

        with open(self.args.output, "wb") as output_fp:
            frame_resp = self.api_sess.get(frame_uri)
            _logger.debug("frame response: %s", frame_resp)

            if frame_resp.status_code != 200:
                _logger.warn("Failed to retrieve frame from url: %s", frame_uri)
            else:
                output_fp.write(frame_resp.content)
                output_fp.flush()
                _logger.info("Succesfully grabbed frame!")

            frame_resp.close()

    @staticmethod
    def __initialize_argument_parser():
        parser = argparse.ArgumentParser(
            description='Pulls footage from a camera on LAN and stores it to the filesystem.')
        parser.add_argument('--api_key', '-a', type=str, required=True,
                            help='Rhombus API key')
        parser.add_argument('--device_id', '-d', type=str, required=True,
                            help='Device Id to pull frame from')
        parser.add_argument('--output', '-o', type=str, required=True,
                            help='The jpg file to write to')
        parser.add_argument('--cert', '-c', type=str, required=False,
                            help='Path to API cert')
        parser.add_argument('--private_key', '-p', type=str, required=False,
                            help='Path to API private key')
        parser.add_argument('--timestamp_ms', '-t', type=int, required=False,
                            help='Timestamp of request image (in milliseconds epoch)')
        parser.add_argument('--permyriad_x', '-px', type=int, required=False, default=0,
                            help='Permyriad (0-10000) x coordinate for cropping')
        parser.add_argument('--permyriad_y', '-py', type=int, required=False, default=0,
                            help='Permyriad (0-10000) y coordinate for cropping')
        parser.add_argument('--permyriad_width', '-pw', type=int, required=False, default=10000,
                            help='Permyriad (0-10000) width for cropping')
        parser.add_argument('--permyriad_height', '-ph', type=int, required=False, default=10000,
                            help='Permyriad (0-10000) height for cropping')
        parser.add_argument('--quality', '-q', type=int, required=False, default=83,
                            help='Jpeg quality')
        parser.add_argument('--downscale', '-s', type=int, required=False, default=1,
                            help='Downscale factor of resulting jpeg, can be 1, 2, 4')
        parser.add_argument('--debug', '-g', required=False, action='store_true',
                            help='Print debug logging')
        return parser


if __name__ == "__main__":
    # this cli command will save a frame from exactly 5 minutes ago of the specified camera
    # python3 get_frame.py -a "<API TOKEN>" -d "<DEVICE ID>" -o frame.jpg
    engine = GetFrame(sys.argv[1:])
    engine.execute()
