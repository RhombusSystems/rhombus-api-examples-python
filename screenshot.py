import requests
from datetime import datetime, timedelta
import time
import json
import urllib3
import webbrowser
import argparse
import sys
import calendar
from urllib import request

# to disable warnings for not verifying host
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class screenshot:
    def __init__(self, cli_args):
        arg_parser = self.__initialize_argument_parser()
        self.args = arg_parser.parse_args(cli_args)
        self.api_url = "https://api2.rhombussystems.com"
        self.api_sess = requests.session()
        self.api_sess.headers = {
            "Accept": "application/json",
            "x-auth-scheme": "api-token",
            "Content-Type": "application/json",
            "x-auth-apikey": self.args.APIkey
        }
        
        self.media_sess = requests.session()
        self.media_sess.headers = {
            "Accept": "application/json",
            "x-auth-scheme": "api-token",
            "Content-Type": "application/json",
            "x-auth-apikey": self.args.APIkey 
        }
        today = datetime.now().replace(microsecond=0, second=0, minute=0)
        self.end_time = today
        self.start_time = (self.end_time - timedelta(days=365))

    @staticmethod
    def __initialize_argument_parser():
        parser = argparse.ArgumentParser(
            description = "Opens a screnshot of a specified time in the webbrowser."
        )
        
        # arguments available for the user to customize
        parser.add_argument('APIkey', type=str, help="Get this from your console.")
        parser.add_argument("Timestamp", type=str, help="Timestamp of screenshot yyyy-mm-dd (0)0:00:00")
        parser.add_argument("CameraName", type=str, help="Name of camera that will produce screenshot.")
        parser.add_argument("-i", "--imageName", type = str, help = "Name of the saved jpeg", default = 'screenshot')
        return parser
       
    # converts the timestamp to ms time
    def milliseconds_time(self, human):
        # the +25200000 is to produce local time and not GMT
        ms_time = (calendar.timegm(time.strptime(human, '%Y-%m-%d %H:%M:%S')) * 1000) + 25200000
        return ms_time 

    # converts the tag name to tag uuid
    def cam_name_convert(self):    
        for value in self.cam_name_data['cameras']:
            if self.args.CameraName == value['name']:
                return value['uuid']

    # returns data with device uuid and device name
    def camera_name(self): 
            endpoint = self.api_url + '/api/camera/getMinimalList'
            payload = {
            }
            resp = self.api_sess.post(endpoint, json=payload,
                            verify=False)
            order_content = resp.content.decode('utf8')
            cam_name_data = json.loads(order_content)
            return cam_name_data

    def screenshot_data(self):
        endpoint = self.api_url + "/api/video/getExactFrameUri"
        timestamp = self.args.Timestamp
        self.ms_time = self.milliseconds_time(timestamp)
        self.cam_name_data = self.camera_name()
        self.uuid = self.cam_name_convert()

        payload = {
            "cameraUuid": self.uuid,
            "timestampMs": self.ms_time
        }

        resp = self.api_sess.post(endpoint, json=payload,
        verify=False)
        content = resp.content
        data = json.loads(content)
        
        return data

    # decrypts the jpg and saves image to a folder
    def saving_img(self):
        resp = self.media_sess.get(self.url,
        verify=False)
        content = resp.content
        # corrects user input
        if '.jpg' in self.args.imageName:
            image_name = self.args.imageName
        else:
            image_name = self.args.imageName + '.jpg'
        # opens the folder and writes the image to it
        with open(image_name, 'wb') as f:
            f.write(content)     # write the data 
            f.close()

    def execute(self):
        self.data = self.screenshot_data()
        if 'frameUri' not in self.data:
            print("Invalid Camera Name")
            return
        else:
            self.url = self.data['frameUri']
            self.saving_img()

if __name__ == "__main__":
    engine = screenshot(sys.argv[1:])
    engine.execute()
