from numpy import longfloat
import requests
import argparse
from datetime import datetime
import json
import sys

class SaveActivityClips:
    #Set up workspace for API calls to Rhombus Systems
    def __init__(self,args):
        #Initialize argument parser
        self.argParser = self.__initArgParser()
        self.args = self.argParser.parse_args(args)

        if not self.args.cooldown:
            self.args.cooldown = 60
        self.args.cooldown = int(self.args.cooldown)*1000

        if not self.args.duration:
            self.args.duration = 604800
        self.args.duration = int(self.args.duration)

        if not self.args.startTime:
            self.args.startTime = datetime.now().timestamp() - self.args.duration
        self.args.startTime = int(self.args.startTime)

        if not self.args.activity:
            self.args.activity = "POSE_ANOMALOUS"
            
        #Create a session to set default call Header information
        self.session = requests.session()
        self.session.headers = {"x-auth-scheme": "api-token","x-auth-apikey": "4kcGBkhPQU-1bjCKiBhFAw"}
        #Set a default base URL for api calls
        self.url = "https://api2.rhombussystems.com/api/"

        self.cameras = []

    #Define arguments which the user may be prompted for
    @staticmethod
    def __initArgParser():
        argParser = argparse.ArgumentParser(description='')
        #argParser.add_argument("apiKey")
        argParser.add_argument("-searchPolicyAlerts","-pa",help = "Search Recent Policy Alerts for Unusual Activity", action="store_true")
        argParser.add_argument("-saveClips","-sc", help = "Saves Clips in console", action="store_true")
        argParser.add_argument("-searchBoundingBoxes","-bb", help = "Search Bounding Boxes for Unusual Activity", action="store_true")
        argParser.add_argument("-duration","-d", help = "Duration of time to search in seconds (default is 7 days or 604800 seconds)")
        argParser.add_argument("-cooldown", "-cd", help = "Minimum time in seconds between saved Bounding Box Frames and reported activity (Default 60)")
        argParser.add_argument("-startTime","-st", help = "Time since epoch in seconds to start searching from")
        argParser.add_argument("-activity","-a", help = "Activity to Search for (defaults to 'POSE_ANOMALOUS')")
        return argParser

    def searchPolicyAlerts(self):
        print("-------------------------------------------")
        print("Searching Policy Alerts for %s" % self.args.activity)
        print("Policy Alert UUID - Time of Alert")
        print("-------------------------------------------")

        #Iterate through each camera and get bounding boxes within defined range
        for camera in self.cameras:
            print(camera.get("name"))

            payload = {
                "deviceUuid": camera.get("uuid"),
                "lastTimestampMs": self.args.startTime*1000
            }
            policyAlertResponse = self.session.post(self.url+"event/getPolicyAlertGroupsForDevice",json = payload)
            if policyAlertResponse.status_code != 200:
                print("Policy Alerts not received as expected (event/getPolicyAlertGroupsForDevice)")
                return
            policyAlertResponse = json.loads(policyAlertResponse.text)
            policyAlertGroups = policyAlertResponse["policyAlertGroups"]
            lastTS = float('inf')
            for alertGroup in policyAlertGroups:
                if alertGroup.get("startTime") < lastTS - self.args.cooldown:
                    lastTS = alertGroup.get("startTime")
                    for alert in alertGroup.get("policyAlerts"):
                        if self.args.activity in alert.get("policyAlertTriggers"):
                            print("\t%s - %s"%(alert.get("uuid"),datetime.fromtimestamp(lastTS/1000).strftime("%m/%d/%y-%H:%M:%S")))
                            if self.args.saveClips:
                                payload = {
                                    "alertUuid": alert.get("uuid"),
                                    "savedClipDescription": "This clip was Saved by a script identifying instances of " +self.args.activity,
                                    "savedClipTitle": "%s-%s-%s.jpg"%((camera.get("uuid"),self.args.activity,datetime.fromtimestamp(lastTS/1000).strftime("%m/%d/%y-%H:%M:%S")))
                                }
                                saveClipResponse = self.session.post(self.url+"event/savePolicyAlertV2", json = payload)
                                if saveClipResponse.status_code != 200:
                                    print("Clip not saved Properly")

    def searchBoundingBoxes(self):
        print("-------------------------------------------")
        print("Searching Bounding Boxes for %s" % self.args.activity)
        print("Times of matching activities")
        print("-------------------------------------------")
        #Iterate through each camera and get bounding boxes within defined range
        for camera in self.cameras:
            print(camera.get("name"))

            payload = {
                "cameraUuid": camera.get("uuid"),
                "startTime": self.args.startTime,
                "duration": self.args.duration
            }
            response = self.session.post(self.url+"camera/getFootageBoundingBoxes",json=payload)
            if response.status_code != 200:
                print("/tFailed to get bounding boxes for %s."%camera.get("name"))
                continue
            response = json.loads(response.text)
            response = response["footageBoundingBoxes"]


            lastTS = 0 #Timestamp of last reported unusual activity frame
            for r in response:#For each bounding box
                eventTimestamp = r.get("ts")
                if r.get("a") == self.args.activity and eventTimestamp > lastTS+self.args.cooldown:#Check timestamp and activity

                    print("\t%s"%datetime.fromtimestamp(eventTimestamp/1000).strftime("%m/%d/%y-%H:%M:%S")) #
                    lastTS = eventTimestamp #Update Time stamp tracker

                    if(self.args.saveClips):
                        payload = {
                            "deviceUuids": [camera.get("uuid")],
                            "description": "This clip was Created by a script identifying instances of " +self.args.activity,
                            "title": "%s - %s" %(self.args.activity,datetime.fromtimestamp(eventTimestamp/1000).strftime("%m/%d/%y-%H:%M:%S")),
                            "durationSec": 10,
                            "startTimeMillis": (longfloat)(lastTS - 5000)
                        }
                        newClip = self.session.post(self.url+"video/spliceV2", json = payload)
                        if newClip.status_code != 200:#Check for unexpected status code
                            print("Failure to create new clip (event/spliceV2)")
                        newClip = json.loads(newClip.text)
                        


    def execute(self):
        if self.args.searchBoundingBoxes or self.args.searchPolicyAlerts:
            #Get list of Cameras to search
            camresponse = self.session.post(self.url+"camera/getMinimalCameraStateList")
            if camresponse.status_code != 200:
                print("Encountered an Error in camera/getMinimalCameraStateList - %i"%camresponse.status_code)
                return
            self.cameras = json.loads(camresponse.text)
            self.cameras = self.cameras["cameraStates"]

        if self.args.searchBoundingBoxes:
            self.searchBoundingBoxes()
        if self.args.searchPolicyAlerts:
            self.searchPolicyAlerts()

if __name__ == "__main__":
    engine = SaveActivityClips(sys.argv[1:])
    engine.execute()
