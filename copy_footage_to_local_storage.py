import requests
import argparse
import sys
import rhombus_logging
from datetime import datetime, timedelta
import urllib3

# just to prevent unnecessary logging since we are not verifying the host
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_logger = rhombus_logging.get_logger("rhombus.CopyFootageToLocalStorage")


class CopyFootageToLocalStorage:
    def __init__(self, cli_args):
        arg_parser = self.__initialize_argument_parser()
        args = arg_parser.parse_args(cli_args)

        if args.debug:
            _logger.setLevel("DEBUG")

        self.api_url = "https://api2.rhombussystems.com"
        self.device_id = args.device_id
        self.output = args.output

        if args.start_time:
            self.start_time = args.start_time
        else:
            now = datetime.now()
            self.start_time = int((now - timedelta(hours=1)).timestamp())
        if args.duration:
            self.duration = args.duration
        else:
            self.duration = 1 * 60 * 60  # 1 hour

        # initialize api http client
        self.api_sess = requests.session()

        # auth scheme changes depending on whether using cert/key or just api token
        if args.cert and args.private_key:
            scheme = "api"
            self.api_sess.cert = (args.cert, args.private_key)
        else:
            scheme = "api-token"

        self.api_sess.headers = {
            "x-auth-scheme": scheme,
            "x-auth-apikey": args.api_key}

        self.api_sess.verify = False

        self.media_sess = requests.session()
        self.media_sess.verify = False

    def execute(self):
        # get a federated session token for media that lasts 1 hour
        session_req_payload = {"durationSec": 60 * 60}
        session_req_resp = self.api_sess.post(self.api_url + "/api/org/generateFederatedSessionToken",
                                              json=session_req_payload)
        _logger.debug("Federated session token response: %s", session_req_resp.content)

        if session_req_resp.status_code != 200:
            _logger.warn("Failed to retrieve federated session token, cannot continue: %s", session_req_resp.content)
            return

        federated_session_token = session_req_resp.json()["federatedSessionToken"]
        session_req_resp.close()

        # get camera media uris
        media_uri_payload = {"cameraUuid": self.device_id}
        media_uri_resp = self.api_sess.post(self.api_url + "/api/camera/getMediaUris",
                                            json=media_uri_payload)
        _logger.debug("Camera media uri response: %s", media_uri_resp.content)

        if session_req_resp.status_code != 200:
            _logger.warn("Failed to retrieve camera media uris, cannot continue: %s", media_uri_resp.content)
            return

        mpd_uri_template = media_uri_resp.json()["lanVodMpdUrisTemplates"][0]
        _logger.debug("Raw mpd uri template: %s", mpd_uri_template)
        media_uri_resp.close()

        """ 
        When we make requests to the camera, the camera will use our session information to serve the correct files.
        The MPD document call starts the session and tells the camera the start time and duration of the clip requested
        We then get the seg_init.mp4 file which has the appropriate mp4 headers/init data
        and then we get the actual video segment files, named seg_1.m4v, seg_2.m4v, where each segment is a 2 second
        segment of video, so we need to go up to seg_<duration/2>.m4v.  The camera will automatically send the correct
        absolute time segments for each of the clip segments.  Concatenating the seg_init.mp4 and seg_#.m4v files into 
        a single .mp4 gives the playable video.
        """

        # the template has placeholders for where the clip start time and duration are supposed to go, so put the
        # desired start time and duration in the template
        mpd_uri = mpd_uri_template.replace("{START_TIME}", str(self.start_time)).replace("{DURATION}",
                                                                                         str(self.duration))
        _logger.debug("Mpd uri: %s", mpd_uri)

        # use the federated session token as our session id for the camera to process our requests
        media_headers = {"Cookie": "RSESSIONID=RFT:" + str(federated_session_token)}

        # start media session with camera by requesting the MPD file
        mpd_doc_resp = self.media_sess.get(mpd_uri, headers=media_headers)
        _logger.debug("Mpd doc: %s", mpd_doc_resp.content)
        mpd_doc_resp.close()

        # start writing the video stream
        with open(self.output, "wb") as output_fp:
            # first write the init file
            init_seg_uri = mpd_uri.replace("clip.mpd", "seg_init.mp4")
            _logger.debug("Init segment uri: %s", init_seg_uri)

            init_seg_resp = self.media_sess.get(init_seg_uri, headers=media_headers)
            _logger.debug("seg_init_resp: %s", init_seg_resp)

            output_fp.write(init_seg_resp.content)
            output_fp.flush()
            init_seg_resp.close()

            # now write the actual video segment files.
            # Each segment is 2 seconds, so we have a total of duration / 2 segments to download
            for cur_seg in range(int(self.duration / 2)):
                seg_uri = mpd_uri.replace("clip.mpd", "seg_" + str(cur_seg) + ".m4v")
                _logger.debug("Segment uri: %s", seg_uri)

                seg_resp = self.media_sess.get(seg_uri, headers=media_headers)
                _logger.debug("seg_resp: %s", seg_resp)

                output_fp.write(seg_resp.content)
                output_fp.flush()
                seg_resp.close()

                # log every 10 minutes of footage downloaded
                if cur_seg > 0 and cur_seg % 300 == 0:
                    _logger.info("Segments written from [%s] - [%s]",
                                 datetime.fromtimestamp(self.start_time + ((cur_seg - 300) * 2)).strftime('%c'),
                                 datetime.fromtimestamp(self.start_time + (cur_seg * 2)).strftime('%c'))

        _logger.info("Succesfully downloaded video from [%s] - [%s] to %s",
                     datetime.fromtimestamp(self.start_time).strftime('%c'),
                     datetime.fromtimestamp(self.start_time + self.duration).strftime('%c'),
                     self.output)

    @staticmethod
    def __initialize_argument_parser():
        parser = argparse.ArgumentParser(
            description='Pulls footage from a camera on LAN and stores it to the filesystem.')
        parser.add_argument('--api_key', '-a', type=str, required=True,
                            help='Rhombus API key')
        parser.add_argument('--device_id', '-d', type=str, required=True,
                            help='Device Id to pull footage from')
        parser.add_argument('--output', '-o', type=str, required=True,
                            help='The MP4 file to write to')
        parser.add_argument('--cert', '-c', type=str, required=False,
                            help='Path to API cert')
        parser.add_argument('--private_key', '-p', type=str, required=False,
                            help='Path to API private key')
        parser.add_argument('--start_time', '-s', type=int, required=False,
                            help='Start time in epoch seconds')
        parser.add_argument('--duration', '-u', type=int, required=False,
                            help='Duration in seconds')
        parser.add_argument('--debug', '-g', required=False, action='store_true',
                            help='Print debug logging')
        return parser


if __name__ == "__main__":
    # this cli command will save the last hour of footage from the specified device
    # python3 copy_footage_to_local_storage.py -a "<API TOKEN>" -d "<DEVICE ID>" -o out.mp4
    engine = CopyFootageToLocalStorage(sys.argv[1:])
    engine.execute()
