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

import requests
import time
import json
import calendar
import csv
import sys
import os
import argparse
import urllib3
import math
from typing import Dict, Set

#to disable warnings for not verifying host
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class FaceVideo:
    processed: Dict[str, Set]

    #initializes the argument parser and the headers for media and the api sessions
    def __init__(self, cli_args):
        arg_parser = self.__initalize_argument_parser()
        self.args = arg_parser.parse_args(cli_args)
        self.api_url = "https://api2.rhombussystems.com"
        self.api_sess = requests.session()
        #api headers
        self.api_sess.headers = {
            "Accept": "application/json",
            "x-auth-scheme": "api-token",
            "Content-Type": "application/json",
            "x-auth-apikey": self.args.APIkey}

        self.media_sess = requests.session()
        #media headers
        self.media_sess.headers = {
            "Accept": "application/json",
            "x-auth-scheme": "api-token",
            "Content-Type": "application/json",
            "x-auth-apikey": self.args.APIkey}
        #The three sets to make sure the similar events are not added to the csv
        self.processed = dict()

    #The argument parser
    @staticmethod
    def __initalize_argument_parser():
        parser = argparse.ArgumentParser(
            description= "Takes a clip from the specified time for a specified duration.")
        #aruements avaiable for the user to customize
        parser.add_argument('APIkey', type=str, help='Get this from your console')
        parser.add_argument('cameraNames', type=str, help='Name of the camera or cameras in the console you want the clips from (ex: camera1, camera2, camera3)')
        parser.add_argument('-s', '--startTime', type=str, help='Add the end search time in yyyy-mm-dd~(0)0:00:00 or default to 30 seconds before current time')
        parser.add_argument('-d', '--duration', type=str, help='What is the duration of the clip in seconds you want', default=30)
        parser.add_argument('-de', '--description', type=str, help= 'Is there a description you want to have for the video', default='This is a clip')
        parser.add_argument('-f', '--format', type = str, help = 'Specify the format of the video', choices=('.mov', '.mp4'), default='.mp4')
        parser.add_argument('-t', '--title', type=str, help='What is the title  or name of the clip', default='Clip')
        parser.add_argument('-r', '--report', type=str, help='Name the file that the clip and csv will go into', default='Report')
        parser.add_argument('-c', '--csv', type=str, help='What do you want to name the csv', default='report')
        parser.add_argument('-u', '--unidentified', type=bool, help='Do you want to see unidentified face events', default= False)
        parser.add_argument('-i', '--identified', type=bool, help='Do you want to see identified face events', default=False)
        parser.add_argument('-hm', '--humanMotion', type=bool, help='Do you want to see human motion', default=False)
        return parser

    #downloads the clip that was made to the computer
    def download(self):
        mediaBaseURL = 'https://media.rhombussystems.com/media/metadata/'
        #url of the api
        endpoint = mediaBaseURL + self.mediaRegion + '/' + self.clipUuid + '.mp4'
        resp = self.media_sess.get(endpoint,
        verify=False)
        content = resp.content
        #opens the file and writes the clip to it
        with open(self.args.report + '/' + self.args.title + self.args.format, 'wb') as f:
            # write the data
            f.write(content)
            f.close()

    #gets the camera data and returns it
    def cameraData(self):
        # url of the api
        endpoint = self.api_url + "/api/camera/getMinimalCameraStateList"
        # any parameters
        payload = {
        }
        resp = self.api_sess.post(endpoint, json=payload,
        verify=False)
        content = resp.content
        data = json.loads(content)
        return data

    #gets the camera uuids from the names
    def camera_uuid(self):
        self.cameraUuids = []
        for value in self.data_camera['cameraStates']:
            for event in self.camera_list:
                if event == value['name']:
                    self.cameraUuids.append(value['uuid'])
    
    #gets the camera names from the 'tu' and returns it for the csv
    def camera_name(self, uuid):
        for event in self.cameraUuids:
            if event in uuid:
                for value in self.data_camera['cameraStates']:
                    if event == value['uuid']:
                        return value['name']

    #converts the timestamp to ms time
    def milliseconds_time(self, human):
        # converts human time to ms. the +25200000 is to get it to local time and not GMT
        ms_time = (calendar.timegm(time.strptime(human, '%Y-%m-%d~%H:%M:%S')) * 1000) + 25200000
        return ms_time

    #creates the clip that the user wants with a specified duration or default 30 seconds
    def clip(self):
        # url of the api
        endpoint = self.api_url + "/api/video/spliceV2"
        if self.args.startTime:
            start = self.milliseconds_time(self.args.startTime)
        else:
            start = int(round((time.time() - (30)) * 1000))
        # any parameters
        payload = {
            "deviceUuids": self.cameraUuids,
            "description": self.args.description,
            "durationSec": self.args.duration,
            "startTimeMillis": start,
            "title": self.args.title
        }
        resp = self.api_sess.post(endpoint, json=payload,
        verify=False)
        content = resp.content
        data = json.loads(content)
        #gets the clipUuid for later use to get the details
        self.clipUuid = data['clipUuid']

    #checks on the progress of the rendering of the clip to make sure it is done before downloading
    def progress(self):
        # url of the api
        endpoint = self.api_url + "/api/event/getClipsWithProgress"
        # any parameters
        payload = {
            "deviceUuidFilters": self.cameraUuids
        }
        resp = self.api_sess.post(endpoint, json=payload,
        verify=False)
        content = resp.content
        data = json.loads(content)
        organized = json.dumps(resp.json(), indent=2, sort_keys=True)
        for value in data['savedClips']:
            if self.clipUuid == value['uuid']:
                if value['status'] == 'COMPLETE':
                    self.mediaRegion = value['clipLocation']['region']
                    return True
                else:
                    return False

    #changes the camera names to a list
    def namesCamera(self):
        self.args.cameraNames = self.args.cameraNames.replace(", ", ",")
        self.camera_list = self.args.cameraNames.split(",")

    #api to get the clip details so the seekpoints can be added to the csv
    def clip_details(self):
        # url of the api
        endpoint = self.api_url + "/api/event/getSavedClipDetails"
        # any parameters
        payload = {
            "clipUuid": self.clipUuid
        }
        resp = self.api_sess.post(endpoint, json=payload,
        verify=False)
        content = resp.content
        data = json.loads(content)
        return data

    def add_to_csv(self, data):
        self.csv_data[self.count].append(data)

    def add_processed(self, event_type, data):
        self.processed[event_type].add(data)

    #checks if the event at that second is already processed
    def already_processed(self, event_type, value, relative_second):
        if(event_type not in self.processed):
            self.processed[event_type] = set()
        processed = self.processed[event_type]
        if(event_type == 'FACE_UNIDENTIFIED'):
            exists = relative_second in processed
            if(not exists):
                self.add_processed(event_type, relative_second)
            return exists
        elif (event_type == 'FACE_IDENTIFIED'):
            exists = relative_second in processed and value['faceName'] in processed
            if(not exists):
                self.add_processed(event_type, relative_second)
                self.add_processed(event_type, value['faceName'])
            return exists
        elif (event_type == 'MOTION_HUMAN'):
            exists = relative_second in processed and self.camera_name(value['tu']) in processed
            if(not exists):
                self.add_processed(event_type, relative_second)
                self.add_processed(event_type, self.camera_name(value['tu']))
            return exists

    #adds the event to csv if not already processed
    def add_event_to_csv(self, value):
        relative_second = abs(math.floor(value['relativeSecond']))
        event_type = value['activity']
        #if it is just motion then it returns
        if(event_type == 'MOTION'): return
        if(not self.already_processed(event_type, value, relative_second)):
            # Add the name
            self.csv_data.append([])
            self.add_to_csv(event_type)
            self.add_to_csv(relative_second)
            if(event_type == 'MOTION_HUMAN'):
                camera_uuid = value['tu']                    
                camera = self.camera_name(camera_uuid)
                self.add_to_csv(camera)
            else:
                self.add_to_csv("")
            if(event_type == 'FACE_IDENTIFIED'):
                face_name = value['faceName']
                self.add_to_csv(face_name)
            self.count += 1

    def csv_add(self, value):
        self.add_event_to_csv(value)
        #opens the csv and writes the data to it   
        with open(self.args.report + '/' + self.args.csv + '.csv', 'w', newline = '') as f:
            writer = csv.writer(f)     # create the csv writer
            writer.writerow(self.header)    # write the header
            writer.writerows(self.csv_data) # write the data

    def execute(self):
        #gets a path and makes a directory file to the path
        path = os.getcwd()
        if (os.path.exists(path + '/' + self.args.report) == False):
            os.mkdir(path + '/' + self.args.report)
        self.data_camera = self.cameraData()
        self.namesCamera()
        self.camera_uuid()
        self.clip()
        print("Clip has been created ans is finishing rendering in the console before downloading")
        while self.progress() == False:
            time.sleep(5)
        self.download()
        print("Clip has finished downloading")
        #checks if the user wants any of the csv data before creating one
        if self.args.unidentified == True or self.args.identified == True or self.args.humanMotion == True:
            self.count = 0
            self.header = ['Event', 'Time in Clip', 'Camera', 'Name(if Applicable)']
            self.csv_data = []
            clipDetails = self.clip_details()
            for value in clipDetails['savedClip']['seekPoints']:
                self.csv_add(value)

if __name__ == "__main__":
    engine = FaceVideo(sys.argv[1:])
    engine.execute()
