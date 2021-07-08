import requests
from datetime import datetime, timedelta
import time
import json
import calendar
import csv
import sys
import os
import argparse
from requests.sessions import default_headers
import urllib3

#to disable warnings for not verifying host
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class timelapseSaver:

    def __init__(self, cli_args):
        arg_parser = self.__initalize_argument_parser()
        self.args = arg_parser.parse_args(cli_args)
        self.api_url = "https://api2.rhombussystems.com"
        self.api_sess = requests.session()
        self.api_sess.headers = {
            "Accept": "application/json",
            "x-auth-scheme": "api-token",
            "Content-Type": "application/json",
            "x-auth-apikey": self.args.APIkey}

        self.media_sess = requests.session()
        self.media_sess.headers = {
            "Accept": "application/json",
            "x-auth-scheme": "api-token",
            "Content-Type": "application/json",
            "x-auth-apikey": self.args.APIkey
        }
        today = datetime.now().replace(microsecond=0, second=0, minute=0)
        self.end_time = today
        self.start_time =  (self.end_time - timedelta(days=365))

    @staticmethod
    def __initalize_argument_parser():
        parser = argparse.ArgumentParser(
            description="Creates a timelapse and saves it in a file"
        )
        #aruements avaiable for the user to customize
        parser.add_argument('APIkey', type=str, help='Get this from your console')
        parser.add_argument('Camera', type=str, help='Which Camera do you want a timelapse from')
        parser.add_argument('-s', '--startTime', type=str, help='Add the end search time in yyyy-mm-dd~(0)0:00:00 or default to 1 day before current time')
        parser.add_argument('-e', '--endTime', type=str, help='Add the end search time in yyyy-mm-dd~(0)0:00:00 or default to current time')
        parser.add_argument('-d', '--vid_duration', type=int, help= 'Specify the duration of the timelapse you want', default=120)
        parser.add_argument('-f', '--format', type = str, help = 'Specify the format of the video', choices=('.mov', '.mp4'), default='.mov')
        parser.add_argument('-t', '--timestamp', type=bool, help='Do you want the timestamp on the timelapse', default=False)
        parser.add_argument('-c', '--camera_details', type=bool, help= 'Do you want the camera details', default=False)
        parser.add_argument('-sw', '--skip_weekends', type=bool, help='Do you want to skip the weekends in the timelapse', default=False)
        parser.add_argument('-sn', '--skip_nights', type=bool, help='Do you want to skip nights in the timelapse', default=False)
        parser.add_argument('-n', '--name', type=str, help='Name the timelapse file', default='timelapse')
        return parser

    def saving_timelapse(self, clipUuid):
        mediaBaseURL = 'https://media.rhombussystems.com/media/timelapse/'
        #url of the api
        endpoint = mediaBaseURL + clipUuid + '.mp4'
        resp = self.media_sess.get(endpoint,
        verify=False)
        content = resp.content
        #opens the file and writes the timelapse to it
        with open(self.args.name + self.args.format, 'wb') as f:
            # write the data
            f.write(content)
            f.close()

    def get_camera_data(self):
        endpoint = self.api_url + "/api/camera/getMinimalCameraStateList"
        payload = {
        }
        resp = self.api_sess.post(endpoint, json=payload,
                        verify=False)
        order_content = resp.content.decode('utf8')
        # Load the JSON to a Python list & dump it back out as formatted JSON
        data = json.loads(order_content)
        return data


    #converts the camera name to a uuid
    def uuid_converter(self, data):
        for value in data['cameraStates']:
                if self.args.Camera == value['name']:
                    uuid = value['uuid']
                    return uuid

    #converts the timestamp to ms time
    def milliseconds_time(self, human):
        # converts human time to ms. the +25200000 is to get it to local time and not GMT
        ms_time = (calendar.timegm(time.strptime(human, '%Y-%m-%d~%H:%M:%S')) * 1000) + 25200000
        return ms_time

    #checks the download progress of the timelapse in the console
    def download_progress(self, clipUuid):
            endpoint = self.api_url + "/api/video/getTimelapseClips"
            payload = {
            }
            resp = self.api_sess.post(endpoint, json=payload,
                        verify=False)
            order_content = resp.content.decode('utf8')
            # Load the JSON to a Python list & dump it back out as formatted JSON
            data = json.loads(order_content)
            #creates a list of just the data of the clip we created
            final_list = [event for event in data['timelapseClips'] if event['clipUuid']==clipUuid]
            for value in final_list:
                #checks if the timelapse is at 100%
                if value['status']['percentComplete'] == 100:
                    return True
                else:
                    return False

    def execute(self):
        # url of the api
        endpoint = self.api_url + "/api/video/generateTimelapseClip"
        #checks if there is a start or end time or just defaults to one day before
        if self.args.startTime:
            start = self.milliseconds_time(self.args.startTime)
        else:
            start = int(round((time.time() - (60 * 60 * 24)) * 1000))
        if self.args.endTime:
            end = self.milliseconds_time(self.args.endTime)
        else:
            end = int(round(time.time() * 1000))

        if end - start < (60*60*1000):
            print("Put a span of at least an hour")
            quit()
        data_camera = self.get_camera_data()
        uuid = self.uuid_converter(data_camera)
        # any parameters
        payload = {
            "deviceUuids": [uuid],
            "drawCameraDetails": self.args.camera_details,
            "drawTimestamp": self.args.timestamp,
            "videoFormat": self.args.format,
            "videoDuration": self.args.vid_duration,
            "skipNights": self.args.skip_nights,
            "skipWeekends": self.args.skip_weekends,
            "startTime": start,
            "stopTime": end
        }
        resp = self.api_sess.post(endpoint, json=payload,
        verify=False)
        content = resp.content
        data = json.loads(content)
        clipUuid = (data['clipUuid'])
        while self.download_progress(clipUuid) == False:
            time.sleep(10)
        self.saving_timelapse(clipUuid)

if __name__ == "__main__":
    engine = timelapseSaver(sys.argv[1:])
    engine.execute()