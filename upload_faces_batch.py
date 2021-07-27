import requests
import argparse
import sys
import json
import csv
import time
import os

class UploadDirectory:
    #Set up workspace for API calls to Rhombus Systems
    def __init__(self,args):
        #Initialize argument parser
        self.argParser = self.__initArgParser()
        self.args = self.argParser.parse_args(args)
        if not self.args.timeOut:
            self.args.timeOut = 300
        #Create a session to set default call Header information
        self.session = requests.session()
        self.session.headers = {"x-auth-scheme": "api-token","x-auth-apikey": self.args.apiKey}
        #Set a default base URL for api calls
        self.url = "https://api2.rhombussystems.com/api/"
        self.startTime = time.time()*1000

    #Define arguments which the user may be prompted for
    @staticmethod
    def __initArgParser():
        argParser = argparse.ArgumentParser(description='Upload a selection of faces for facial recognition. List file names in a CSV on individual lines.Please follow the nameing protocal: First-Last_#.jpg')
        argParser.add_argument("apiKey", help="Get this from your Console.")
        argParser.add_argument("addr", help="Local Address of photo directory (photos must follow format first-last_x.jpg) or csv with comma separated photo info (addr,name)")
        argParser.add_argument("-time","-t", help="Include Timestamp in Report title", action='store_true')
        argParser.add_argument("-timeOut","-to", help="Number of seconds before timeout")
        return argParser

    def execute(self):
        ##Upload Faces to prelaod facial ID
        #Parse through CSV or Folder
        uploadedFaces = []
        if self.args.addr.endswith('.csv'):
            try:
                with open(self.args.addr) as csvInput:
                    inputReader = csv.reader(csvInput)
                    for row in inputReader:
                        if len(row) != 2:
                            continue
                        faceAddr = str(row[0])#Address of face
                        fileName = str(row[1])#Name to be Associated with Face
                        try:
                            #Attempt upload of face
                            files = {"files[]": (fileName, open(faceAddr, "rb"), "image/jpeg")}
                            uploadResponse = self.session.post(self.url+'upload/faces',files=files)
                            #Report unexpected status codes
                            if(uploadResponse.status_code != 201):
                                print("Error encountered while uploading face:",faceAddr,"(/api/upload/faces)")
                                continue
                            #Store name and filename for verification            
                            uploadedFaces.append(fileName)
                        except FileNotFoundError:#Catch non valid faces, and continue
                            print(faceAddr,"is not a valid jpg.")
                            continue
            except FileNotFoundError:
                print("FileNotFoundError: Indicated CSV file is non existent.")
                return
        else:#If provided addr is a folder, attempt to upload all jpg in folder
            for fileName in os.listdir(self.args.addr):  
                if fileName.endswith(".jpg") or fileName.endswith(".jpeg"):
                    faceAddr = self.args.addr + fileName

                    #Ensure fileName follows First-last_x format
                    fileName = fileName.split(".")[0]
                    fileName = fileName.split("_")#[first-last,x]
                    if len(fileName) != 2:#if not name and number
                        continue
                    if not fileName[1].isdigit():#if x is not a number
                        continue
                    if len(fileName[0].split("-")) != 2:#if not first and last names
                        continue
                    fileName = fileName[0].replace("-"," ")
                    
                    try:
                        #Attempt upload of face
                        files = {"files[]": (fileName, open(faceAddr, "rb"), "image/jpeg")}
                        uploadResponse = self.session.post(self.url+'upload/faces',files=files)
                        #Report unexpected status codes
                        if(uploadResponse.status_code != 201 and uploadResponse.status_code != 429):
                            print("Error encountered while uploading face:",faceAddr,"(/api/upload/faces)")
                            continue
                        #Store name and filename for verification            
                        uploadedFaces.append(fileName)
                    except FileNotFoundError:#Catch non valid faces, and continue
                        print(faceAddr,"is not a valid jpg.")
                        continue
        print(uploadedFaces)
        #Poll Endpoint or Timeout
        ##Check status of uploaded faces
        #record status for output
        pollStartTime = time.time()
        uploadStatus = []
        while time.time() - pollStartTime < self.args.timeOut and len(uploadedFaces):
            uploadStatusResponse = self.session.post(self.url+"face/getUploadedFaces")
            #Check for unexpected behavior
            if(uploadStatusResponse.status_code != 200):
                print("Error encountered while getting Uploaded Faces (/api/face/getUploadedFaces) - %i." % uploadStatusResponse.status_code)

            uploadStatusResponse = json.loads(uploadStatusResponse.text)
            uploadStatusResponse = uploadStatusResponse.get("uploadedFaces")
            if uploadStatusResponse == None:
                continue
            for face in uploadStatusResponse:
                if face.get("createdAtMillis") > self.startTime:
                    if face.get("name") in uploadedFaces:
                        uploadStatus.append(face)
                        uploadedFaces.remove(face.get("name"))
                else:
                    break

        #Declare Fields and Populate Rows for output to CSV
        fields = ['Filename','Upload Status','Error Message']
        rows = []
        for i in range(len(uploadStatus)):
            try:
                #If the face at the current index of uploadStatus is not from the current directory upload
                #a ValueError exception is thrown and the face is skipped
                #Extract the stored filename to compare
                picID = uploadStatus[i]["origS3Key"]
                picID = picID.split("/")
                picID = picID[len(picID)-1]

                #Status returns a boolean, convert to string for output and fill detail info if needed
                #Faces are rejected if they are not the correct file type or fail to meet requirements
                status = uploadStatus[i]["success"]
                if(status):
                    status = " Success"
                    details = ""
                else:
                    status = " Failure"
                    details = " " + uploadStatus[i]["errorMsg"]

                #add row to rows
                rows.append([picID,status,details])
            except ValueError:
                continue

        #add failure report for any faces that were unaccounted for
        for face in uploadedFaces:
            rows.append([face[0],"Fail","Failure to Upload"])

        #Select name for report file 
        if(self.args.time):
            outputFilename = "faceReport("+time.asctime(time.localtime())+").csv"
        else:
            outputFilename = "faceReport.csv"
        #write report file
        with open(outputFilename, 'w') as csvOutput:
            outputWriter = csv.writer(csvOutput)
            outputWriter.writerow(fields)
            outputWriter.writerows(rows)
        return

if __name__ == "__main__":
    engine = UploadDirectory(sys.argv[1:])
    engine.execute()
