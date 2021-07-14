import requests
from datetime import datetime, timedelta
import time
import json
import calendar
import csv
import sys
import os
import argparse
import urllib3
import subprocess as sp

#to disable warnings for not verifying host
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class killSwitch():
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
        
    @staticmethod
    def __initalize_argument_parser():
        parser = argparse.ArgumentParser(
            description= "Kill Switch")
        #aruements avaiable for the user to customize
        parser.add_argument('APIkey', type=str, help='Get this from your console')
        parser.add_argument('-a', '--Alias', type=str, help='What is the alias of the string')
        parser.add_argument('-i', '--Host', type=str, help='What is the host ip of the strip')
        parser.add_argument('cameraName', type=str, help='Name of camera')
        parser.add_argument('Plug', type=int, help='What plug do you want to turn on or off')
        parser.add_argument('label', type=str, help='What is the label that is safe to use the monitor')
        return parser
    

    # Turns off the plug in the power strip
    def switch(self):
        if self.args.Host:
            output = sp.getoutput('kasa --strip --host ' + self.args.Host + ' ' + 'off' + ' --index ' + str(self.args.Plug - 1 ))
        elif self.args.Alias:
            output = sp.getoutput('kasa --strip --alias ' + self.args.Alias + ' ' + 'off' + ' --index ' + str(self.args.Plug - 1))
        else:
            print('Please put a host or an alias name.')
            quit()
        
    #gets the api data about the cameras in the console and returns it
    def camera_data(self):
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
    
    # converts camera name to a Uuid
    def camera_uuid(self):
        data_camera = self.camera_data()
        for value in data_camera['cameraStates']:
            if self.args.cameraName == value['name']:
                self.cameraUuids = value['uuid']
    
    # Gets the seek points from 3 min ago and puts the names in a set
    def recent_face_seekpoints(self, start_time, duration):
        # url of the api
        endpoint = self.api_url + "/api/camera/getFootageSeekpointsV2"
        payload = {
            "startTime": start_time,
            "duration": duration,
            "cameraUuid": self.cameraUuids
        }
        resp = self.api_sess.post(endpoint, json=payload,
        verify=False)
        content = resp.content
        data = json.loads(content)
        processed: set[str] = set()  # creates an empty set
        data = [event for event in data['footageSeekPoints'] if event['a'] == "FACE_IDENTIFIED"]
        for value in data:
            name = value['fn']
            if name not in processed:
                processed.add(name)  # appends values to the set
        return processed

    # gets all the labels in the org
    def label_data(self):
        endpoint = self.api_url + "/api/face/getFaceLabelsForOrg"    # url of the api
        payload = {
        }
        resp = self.api_sess.post(endpoint, json=payload,
        verify=False)
        content = resp.content
        data = json.loads(content)
        return data

    # converts the name to a label
    def face_label_convert(self, labels, value):
        if value in labels['faceLabels']:
            label = labels['faceLabels'][value]
            return label

    def execute(self):
        self.camera_uuid()
        running = True
        while running == True:
            end_time = int(round(time.time() * 1000))  # constantly current time
            start_time = end_time - 180000          # Start time is 3 min behind current time
            duration = end_time - start_time
            names = self.recent_face_seekpoints(start_time, duration) # set of the people who have been identified
            labels = self.label_data()
            if (len(names) == 0):
                print("Processing ...")
            else:
                for value in names:
                    label = self.face_label_convert(labels, value)
                    if label != [self.args.label]:    # self.args.label is the "safe label" - will not turn off device
                        self.switch()     # Turns off the plug in the power strip
                        print("Processed")
                        running = False
                    else:
                        print("Processing ...")
            time.sleep(15)   # wait 15 seconds before each run through
            
if __name__ == "__main__":
    engine = killSwitch(sys.argv[1:])
    engine.execute()
