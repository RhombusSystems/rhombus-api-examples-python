import requests
import argparse
from datetime import datetime
import json
import sys

class sharedMediaReport:
    #Set up workspace for API calls to Rhombus Systems
    def __init__(self,args):
        #Initialize argument parser
        self.argParser = self.__initArgParser()
        self.args = self.argParser.parse_args(args)
        #Create a session to set default call Header information
        self.session = requests.session()
        self.session.headers = {"x-auth-scheme": "api-token","x-auth-apikey": self.args.apiKey}
        #Set a default base URL for api calls
        self.url = "https://api2.rhombussystems.com/api/"
        self.curTime = int(datetime.utcnow().timestamp())

    #Define arguments which the user may be prompted for
    @staticmethod
    def __initArgParser():
        argParser = argparse.ArgumentParser(description='Generates a simple report on the status of shared media within the organization')
        argParser.add_argument("apiKey", help = 'Your personal api key, get this from your Rhombus Console')
        return argParser
    
    def execute(self):
        #Collect Data and ensure expected status codes are received
        response = self.session.post(self.url+"event/getSharedClipGroupsV2")
        if response.status_code != 200:
            print("Encountered an Error")
            return
        sharedClipGroups = json.loads(response.text)
        sharedClipGroups = sharedClipGroups["sharedClipGroups"]

        response = self.session.post(self.url+"video/getSharedTimelapseGroups")
        if response.status_code != 200:
            print("Encountered an Error")
            return
        sharedTimelapseGroups = json.loads(response.text)
        sharedTimelapseGroups = sharedTimelapseGroups["sharedTimelapses"]

        #Camera UUIDs are needed to check for open streams
        response = self.session.post(self.url+"camera/getMinimalList")
        if response.status_code != 200:
            print("Encountered an Error")
            return
        cameras = json.loads(response.text)
        cameras = cameras["cameras"]

        sharedStreams = []
        for camera in cameras:#For each camera, check for any open streams
            payload = {"cameraUuid":camera.get("uuid")}
            response = self.session.post(self.url+"camera/findSharedLiveVideoStreams",json = payload)
            if response.status_code != 200:
                print("Encountered an Error")
                return
            response = json.loads(response.text)
            response = response["sharedLiveVideoStreams"]
            if response is None:#If no streams, continue
                continue
            for stream in response:#If streams, add to list
                sharedStreams.append(stream)

        print("--------------------------------------------------------------")
        print("| Shared Media Report                                        |")
        print("--------------------------------------------------------------")
        print("Shared Streams")
        if sharedStreams:
            print("\tCamera UUID, Password Protected, Start Time, End Time, URL")
            for s in sharedStreams:
                print("\t%s, %s, %s, %s, %s" % (s.get("cameraUuid"),s.get("passwordProtected"),int(s.get("timestampMs")/1000),s.get("expirationTime"),s.get("sharedLiveVideoStreamUrl")))
                if not s.get("passwordProtected"):
                    print("\t\t Flag Unsecured Stream")
                if not s.get("expirationTime"):
                    print("\t\t Flag Unlimited Stream")
        else:
            print("\tNo Shared Streams")
        print("Shared Clip Groups")
        if sharedClipGroups:
            print("\tTitle, Description, Password Protected, Created at, Expires at")
            for cg in sharedClipGroups:
                print("\t%s, %s, %s, %s, %s" % (cg.get("title"),cg.get("description"),cg.get("isSecured"),int(cg.get("createdAtMillis")/1000),cg.get("expirationTimeSecs")))
                if not cg.get("isSecured"):
                    print("\t\t Flag Unsecured Clip Group")
                if not cg.get("expirationTime"):
                    print("\t\t Flag Unlimited Clip Group")
        else:
            print("\tNo Shared Clip Groups")
        print("Shared Timelapse Groups")
        if sharedTimelapseGroups:
            print("\tTitle, Description, Password Protected, Created at, Expires at")
            for tg in sharedTimelapseGroups:
                print("\t%s, %s, %s, %s, %s" % (tg.get("title"),tg.get("description"),tg.get("isSecured"),int(tg.get("createdAtMillis")/1000),tg.get("expirationTimeSecs")))
                if not tg.get("isSecured"):
                    print("\t\t Flag Unsecured Timelapse Group")
                if not tg.get("expirationTime"):
                    print("\t\t Flag Unlimited Timelapse Group")
        else:
            print("\tNo Shared Timelapse Groups")
if __name__ == "__main__":
    engine = sharedMediaReport(sys.argv[1:])
    engine.execute()