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

def argparser():
    my_parser = argparse.ArgumentParser()

    #aruements avaiable for the user to customize
    my_parser.add_argument('APIkey', type=str, help='Get this from your console')
    my_parser.add_argument('Camera', type=str, help='Which Camera do you want a timelapse from')
    my_parser.add_argument('-s', '--startTime', type=str, help='Add the end search time in yyyy-mm-dd~(0)0:00:00 or default to 1 day before current time')
    my_parser.add_argument('-e', '--endTime', type=str, help='Add the end search time in yyyy-mm-dd~(0)0:00:00 or default to current time')
    my_parser.add_argument('-d', '--vid_duration', type=int, help= 'Specify the duration of the timelapse you want', default=120)
    my_parser.add_argument('-f', '--format', type = str, help = 'Specify the format of the video', choices=('.mov', '.mp4'), default='.mp4')
    my_parser.add_argument('-t', '--timestamp', type=bool, help='Do you want the timestamp on the timelapse', default=False)
    my_parser.add_argument('-c', '--camera_details', type=bool, help= 'Do you want the camera details', default=False)
    my_parser.add_argument('-sw', '--skip_weekends', type=bool, help='Do you want to skip the weekends in the timelapse', default=False)
    my_parser.add_argument('-sn', '--skip_nights', type=bool, help='Do you want to skip nights in the timelapse', default=False)
    my_parser.add_argument('-n', '--name', type=str, help='Name the timelapse file', default='timelapse')

    args = my_parser.parse_args()
    return args

args = argparser()

def saving_timelapse(uuid):
    if __name__ == "__main__":
        baseURL = 'https://media.rhombussystems.com/media/timelapse/'
        #url of the api
        endpoint = baseURL + uuid + '.mp4'

        api_key = args.APIkey

        sess = requests.session()

        today = datetime.now().replace(microsecond=0, second=0, minute=0)
        end_time = today
        start_time =  (end_time - timedelta(days=365))

        sess.headers = {
            "x-auth-scheme": "api-token",
            "x-auth-apikey": api_key
        }
        resp = sess.get(endpoint,
        verify=False)
        content = resp.content
        #opens the file and writes the timelapse to it
        with open(args.name + args.format, 'wb') as f:
            # write the data
            f.write(content)
            f.close()

def get_camera_data():
    if __name__ == "__main__":
        endpoint = "https://api2.rhombussystems.com/api/camera/getMinimalCameraStateList"
        api_key = args.APIkey
        sess = requests.session()
        today = datetime.now().replace(microsecond=0, second=0, minute=0)
        end_time = today
        start_time = (end_time - timedelta(days=365))
        payload = {
        }
        sess.headers = {
            "Accept": "application/json",
            "x-auth-scheme": "api-token",
            "Content-Type": "application/json",
            "x-auth-apikey": api_key}
        resp = sess.post(endpoint, json=payload,
                        verify=False)
        order_content = resp.content.decode('utf8')
        # Load the JSON to a Python list & dump it back out as formatted JSON
        data = json.loads(order_content)
        return data

#converts the camera name to a uuid
def uuid_converter(data):
    for value in data['cameraStates']:
            if args.Camera == value['name']:
                uuid = value['uuid']
                return uuid

#converts the timestamp to ms time
def milliseconds_time(human):
    # converts human time to ms. the +25200000 is to get it to local time and not GMT
    ms_time = (calendar.timegm(time.strptime(human, '%Y-%m-%d~%H:%M:%S')) * 1000) + 25200000
    return ms_time

#checks the download progress of the timelapse in the console
def download_progress(clipUuid):
    if __name__ == "__main__":
        endpoint = "https://api2.rhombussystems.com/api/video/getTimelapseClips"
        api_key = args.APIkey
        sess = requests.session()
        today = datetime.now().replace(microsecond=0, second=0, minute=0)
        end_time = today
        start_time = (end_time - timedelta(days=365))
        payload = {
        }
        sess.headers = {
            "Accept": "application/json",
            "x-auth-scheme": "api-token",
            "Content-Type": "application/json",
            "x-auth-apikey": api_key}
        resp = sess.post(endpoint, json=payload,
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

def generate_timelapse():
    if __name__ == "__main__":
        # url of the api
        endpoint = "https://api2.rhombussystems.com/api/video/generateTimelapseClip"
        api_key = args.APIkey
        sess = requests.session()
        today = datetime.now().replace(microsecond=0, second=0, minute=0)
        end_time = today
        start_time =  (end_time - timedelta(days=365))
        #checks if there is a start or end time or just defaults to one day before
        if args.startTime:
            start = milliseconds_time(args.startTime)
        else:
            start = int(round((time.time() - (60 * 60 * 24)) * 1000))
        if args.endTime:
            end = milliseconds_time(args.endTime)
        else:
            end = int(round(time.time() * 1000))
        data_camera = get_camera_data()
        uuid = uuid_converter(data_camera)
        # any parameters
        payload = {
            "deviceUuids": [uuid],
            "drawCameraDetails": args.camera_details,
            "drawTimestamp": args.timestamp,
            "videoFormat": args.format,
            "videoDuration": args.vid_duration,
            "skipNights": args.skip_nights,
            "skipWeekends": args.skip_weekends,
            "startTime": start,
            "stopTime": end
        }
        sess.headers = {
            "x-auth-scheme": "api-token",
            "x-auth-apikey": api_key
        }
        resp = sess.post(endpoint, json=payload,
        verify=False)
        content = resp.content
        data = json.loads(content)
        clipUuid = (data['clipUuid'])
        while download_progress(clipUuid) == False:
            time.sleep(5)
        
        saving_timelapse(clipUuid)

def main():
    generate_timelapse()

main()