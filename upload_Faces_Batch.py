import requests
import argparse
import sys
import json
import csv
import time

class uploadDirectory:
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
        argParser = argparse.ArgumentParser(description='Upload a selection of faces for facial recognition. List file names in a CSV on individual lines.Please follow the nameing protocal: First-Last_#.jpg')
        argParser.add_argument("apiKey", help="Get this from your Console.")
        argParser.add_argument("addr", help="Local Address of Photo Directory CSV")
        argParser.add_argument("-time","-t", help="Include Timestamp in Report title", action='store_true')
        return argParser

    def execute(self):
        ##Upload Faces to prelaod facial ID
        #Parse through CSV or Folder
        uploadedFaces = []
        try:
            with open(self.args.addr) as csvInput:
                inputReader = csv.reader(csvInput)
                for row in inputReader:
                    faceAddr = str(row[0])#Address of face
                    fileName = faceAddr.split("/")
                    fileName = fileName[len(fileName)-1]#Filename of face
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
                        print(fileName,"is not a valid jpg.")
                        continue
        except FileNotFoundError:
            print("FileNotFoundError: Indicated CSV file is non existent.")
            return

        #Pause to allow faces to be processed
        time.sleep(30)
        ##Check status of uploaded faces
        #record status for output
        uploadStatusResponse = self.session.post(self.url+"face/getUploadedFaces")
        #Check for unexpected behavior
        if(uploadStatusResponse.status_code != 200):
            print("Error encountered while getting Uploaded Faces (/api/face/getUploadedFaces).")

        uploadStatus = json.loads(uploadStatusResponse.text)
        uploadStatus = uploadStatus["uploadedFaces"]
        

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

                #Throws an exception if the face and picture do not match with uploaded
                uploadedFaces.index(picID)
                uploadedFaces.remove(picID)

                #Status returns a boolean, convert to string for output and fill detail info if needed
                #Faces are rejected if they are not the correct file type or fail to meet requirements
                status = uploadStatus[i]["success"]
                if(status):
                    status = " Success"
                    details = " -"
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
    engine = uploadDirectory(sys.argv[1:])
    engine.execute()