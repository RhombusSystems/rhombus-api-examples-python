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
        parser.add_argument('--APIkey', type=str, help='Get this from your console', default='9Ts3iQ_HSZGHEqwxZnPKpA')
        parser.add_argument('-a', '--Alias', type=str, help='What is the alias of the string')
        parser.add_argument('-i', '--Host', type=str, help='What is the host ip of the strip')
        parser.add_argument('cameraName', type=str, help='Name of camera')
        parser.add_argument('Plug', type=int, help='What plug do you want to turn on or off')
        parser.add_argument('label', type=str, help='What is the label that is safe to use the monitor')

        return parser
    
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
    
    def camera_uuid(self):
        data_camera = self.camera_data()
        self.cameraUuids = []
        for value in data_camera['cameraStates']:
            for event in self.camera_list:
                if event == value['name']:
                    self.cameraUuids.append(value['uuid'])
                
    def namesCamera(self):
        self.args.cameraName = self.args.cameraName.replace(", ", ",")
        self.camera_list = self.args.cameraName.split(",")
    
    def recent_faces(self, start_time, end_time):
        # url of the api
        endpoint = self.api_url + "/api/face/getRecentFaceEventsV2"
        payload = {
        "filter": {
            "deviceUuids": self.cameraUuids,
            "types": ["named"]   # won't need this in later version
            },
        "interval": {
            "end": end_time,
            "start": start_time
            }
        }
        resp = self.api_sess.post(endpoint, json=payload,
        verify=False)
        content = resp.content
        data = json.loads(content)

        processed: set[str] = set()  # creates an empty set
        for value in data['faceEvents']:
            name = value['faceName']
            if name not in processed:
                processed.add(name)  # appends values to the set
        return processed

    def label_data(self):
        endpoint = self.api_url + "/api/face/getFaceLabelsForOrg"    # url of the api
        payload = {
        }
        resp = self.api_sess.post(endpoint, json=payload,
        verify=False)
        content = resp.content
        data = json.loads(content)
        return data

    def face_label_convert(self, labels, value):
        if value in labels['faceLabels']:
            label = labels['faceLabels'][value]
            return label

    def execute(self):
        self.namesCamera()
        self.camera_uuid()
        running = True
        while running == True:
            end_time = int(round(time.time() * 1000))  # constantly current time
            start_time = end_time - 60000              # constantly one minute before current time
            names = self.recent_faces(start_time, end_time) # set of the people who have been identified
            if len(names) == 0:
                print("Processing ... ")  
            else:
                labels = self.label_data()
                for value in names:
                    label = self.face_label_convert(labels, value)
                    if label != [self.args.label]:    # self.args.label is the "safe label" - will not turn off device
                        self.switch()
                        print("Processed")
                        running = False
            time.sleep(1)   # wait one second before each run through
            
if __name__ == "__main__":
    engine = killSwitch(sys.argv[1:])
    engine.execute()
