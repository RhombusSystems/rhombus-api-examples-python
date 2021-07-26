import requests
import argparse
import sys
import json
from datetime import datetime, timedelta
import time
#This script runs a quick report on the status of all cameras in an organization, report includes name,uuid,status and details if there are any
class cameraStatus:
    #Set up workspace for API calls to Rhombus Systems
    def __init__(self,args):
        #Initialize argument parser and parse command line arguments
        self.argParser = self.__initArgParser()
        self.args = self.argParser.parse_args(args)
        #Create a session to set default call Header information. 
        #This verifies to the Rhombus servers that we have authorization to access the API
        self.session = requests.session()
        self.session.headers = {"x-auth-scheme": "api-token","x-auth-apikey": self.args.apiKey}
        #Set a default base URL for api calls
        self.url = "https://api2.rhombussystems.com/api/"
    def getStatus(self):
        #Get a list of all cameras in the org
        sysStatus = self.session.post(self.url+"camera/getMinimalList")
        #Check status code to ensure that the expected response was received
        if sysStatus.status_code != 200:
            print("Error in /api/camera/getMinimalList")
            return 0
        else:
            #print formating details for this scripts output
            print("CAMERA NAME (UUID): STATUS - STATUS DETAILS")
            #convert the response into a easily traversable list
            parseSysStatus = json.loads(sysStatus.text)
            parseSysStatus = parseSysStatus["cameras"]

            for camera in parseSysStatus:
                uuid = camera["uuid"]
                if(self.args.uuid): #If a camera uuid was specified
                    if(self.args.uuid != uuid): #If the current uuid is not equivalent to the expected uuid
                        continue #skip to next camera without storing other data
                status = camera["healthStatus"]
                detail = camera["healthStatusDetails"]
                if detail == "NONE":
                    detail = ''
                else:
                    detail = " - " + detail
                name = camera["name"]
                #This segment could be quickly expanded to report many more fields
                
                print(name + "(" + uuid + "): " + status + detail)

                ##If camera is offline, get uptime information for a basic report
                if(status == "RED"):
                    #Create payload for API call to guarantee that the most recent uptime window will be included
                    payload = {
                        "cameraUuid": uuid,
                        "endTime": time.time() * 1000, #Current Time in MS since Epoch
                        "startTime": 1420113600000 #MS since Epoch of a time in 2015 which predates Rhombus
                        }

                    camUpTime = self.session.post(self.url+"camera/getUptimeWindows",json = payload)
                    #Check status code to ensure that the expected response was received
                    if sysStatus.status_code != 200:
                        print("\tUnable to verify downtime")
                        continue
                    else:
                        #Prepare response for parsing
                        parseCamUptime = json.loads(camUpTime.text)
                        parseCamUptime = parseCamUptime["uptimeWindows"][len(parseCamUptime["uptimeWindows"])-1]

                        #Get start and duration information for the most recent window of uptime
                        startTime = parseCamUptime["startSeconds"]
                        duration = parseCamUptime["durationSeconds"]
                        lastOn = startTime+duration #time at which point the camera was last online
                        #Display lastOn and time elapsed since to the user
                        print("\tOffline since: " + datetime.fromtimestamp(lastOn).strftime("%m/%d/%y, %H:%M"))
                        print("\tDown for: "+ str(timedelta(seconds = time.time() - lastOn)))
    #Define arguments which the user may be prompted for
    @staticmethod
    def __initArgParser():
        argParser = argparse.ArgumentParser(description = "This script displays information about the status of all or a selected camera. It provides the name, uuid, status and status details alongside other helpful statistics")
        argParser.add_argument("apiKey", help = "Get this from your Console.")
        argParser.add_argument("--uuid", help = "Display only the status of the camera with a matching uuid")
        return argParser
        
if __name__ == "__main__":
    engine = cameraStatus(sys.argv[1:])
    engine.getStatus()
