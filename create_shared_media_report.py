import requests
import argparse
import json
import sys
import time

class SharedMediaReport:
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

    #Define arguments which the user may be prompted for
    @staticmethod
    def __initArgParser():
        argParser = argparse.ArgumentParser(description='Generates a simple report on the status of shared media within the organization')
        argParser.add_argument("apiKey", help = 'Your personal api key, get this from your Rhombus Console')
        argParser.add_argument("--removeSharedClipGroup","--rc", help = "UUID of Clip Group to remove")
        argParser.add_argument("--removeSharedTimelapseGrop","--rt", help = "UUID of Timelapse Group to remove")
        argParser.add_argument("--removeSharedStream","--rs", help = "UUID of Camera and UUID of stream to remove, comma separated")
        return argParser

    #This collection of methods simply attempt to remove shared Media as identified by CLAs
    def removeClipGroup(self,uuid):
        payload = {"uuid":uuid}
        self.session.post(self.url+"event/deleteSharedClipGroupV2", json = payload)
    def removeTimelapseGroup(self,uuid):
        payload = {"uuid":uuid}
        self.session.post(self.url+"video/deleteSharedTimelapseGroup", json = payload)
    def removeStream(self,uuids):
        if len(uuids) != 2:
            print("Too many/few arguments included to remove stream")
            return
        payload = {
            "cameraUuid":uuids[0],
            "uuid":uuids[1]
            }
        self.session.post(self.url+"camera/deleteSharedLiveVideoStream", json = payload)

    def execute(self):
        #Attempt to remove methods as requested by user
        if(self.args.removeSharedClipGroup):
            self.removeClipGroup(self.args.removeSharedClipGroup)
        if(self.args.removeSharedTimelapseGrop):
            self.removeTimelapseGroup(self.args.removeSharedTimelapseGrop)
        if(self.args.removeSharedStream):
            self.removeStream(self.args.removeSharedStream.split(","))

        #Collect Data and ensure expected status codes are received
        response = self.session.post(self.url+"event/getSharedClipGroupsV2")
        if response.status_code != 200:
            print("Encountered an Error in event/getSharedClipGroupsV2 - %i"%response.status_code)
            sharedClipGroups = None
        else:
            sharedClipGroups = json.loads(response.text)
            sharedClipGroups = sharedClipGroups["sharedClipGroups"]

        response = self.session.post(self.url+"video/getSharedTimelapseGroups")
        if response.status_code != 200:
            print("Encountered an Error in video/getSharedTimelapseGroups - %i"%response.status_code)
            sharedTimelapseGroups = None
        else:
            sharedTimelapseGroups = json.loads(response.text)
            sharedTimelapseGroups = sharedTimelapseGroups["sharedTimelapses"]

        #Camera UUIDs are needed to check for open streams
        response = self.session.post(self.url+"camera/getMinimalCameraStateList")
        if response.status_code != 200:
            print("Encountered an Error in camera/getMinimalCameraStateList - %i"%response.status_code)
            return
        cameras = json.loads(response.text)
        cameras = cameras["cameraStates"]

        sharedStreams = []
        for camera in cameras:#For each camera, check for any open streams
            if camera.get("liveStreamShared"):
                while True:
                    payload = {"cameraUuid":camera.get("uuid")}
                    response = self.session.post(self.url+"camera/findSharedLiveVideoStreams",json = payload)
                    if response.status_code == 429:#If request is rate limited
                        time.sleep(response.headers.get("Retry-After"))#Wait for "Retry-After"
                    elif response.status_code == 200:#If response is successful, break from loop
                        break
                    else:#If request was not rate limited or successful, move to next camera
                        print("Encountered an unexpected status code in camera/findSharedLiveVideoStreams - %i"%response.status_code)
                        continue
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
            print("\tCamera UUID, Stream UUID, Password Protected, Start Time, End Time, URL")
            for s in sharedStreams:
                print("\t%s,%s, %s, %s, %s, %s" % (s.get("cameraUuid"),s.get("uuid"),s.get("passwordProtected"),int(s.get("timestampMs")/1000),s.get("expirationTime"),s.get("sharedLiveVideoStreamUrl")))
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
                print("\t%s, %s, %s, %s, %s, %s" % (cg.get("uuid"),cg.get("title"),cg.get("description"),cg.get("isSecured"),int(cg.get("createdAtMillis")/1000),cg.get("expirationTimeSecs")))
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
                print("\t%s, %s, %s, %s, %s, %s" % (tg.get("uuid"),tg.get("title"),tg.get("description"),tg.get("isSecured"),int(tg.get("createdAtMillis")/1000),tg.get("expirationTimeSecs")))
                if not tg.get("isSecured"):
                    print("\t\t Flag Unsecured Timelapse Group")
                if not tg.get("expirationTime"):
                    print("\t\t Flag Unlimited Timelapse Group")
        else:
            print("\tNo Shared Timelapse Groups")
if __name__ == "__main__":
    engine = SharedMediaReport(sys.argv[1:])
    engine.execute()
