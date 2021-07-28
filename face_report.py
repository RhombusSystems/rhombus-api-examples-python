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

#to disable warnings for not verifying host
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class faceProject:
    def __init__(self, cli_args):
        arg_parser = self.__initalize_argument_parser()
        self.args = arg_parser.parse_args(cli_args)
        self.api_url = "https://api2.rhombussystems.com"
        self.api_sess = requests.session()
        self.api_sess.headers = {
            "x-auth-scheme": "api-token",
            "x-auth-apikey": self.args.APIkey}

        self.media_sess = requests.session()
        self.media_sess.headers = {
            "x-auth-scheme": "api-token",
            "x-auth-apikey": self.args.APIkey}
        today = datetime.now().replace(microsecond=0, second=0, minute=0)
        self.end_time = today
        self.start_time =  (self.end_time - timedelta(days=365))

    @staticmethod
    def __initalize_argument_parser():
        parser = argparse.ArgumentParser(
            description= "Gets a report of the recent faces and downloads the pictures of each face."
        )

        #aruements avaiable for the user to customize
        parser.add_argument('--APIkey', type=str, help='Get this from your console')
        parser.add_argument('-s', '--startTime', type=str, help='Add the end search time in yyyy-mm-dd~(0)0:00:00 or default to 1 hour before current time')
        parser.add_argument('-e', '--endTime', type=str, help='Add the end search time in yyyy-mm-dd~(0)0:00:00 or default to current time')
        parser.add_argument('-f', '--filter', type=str, help= 'Choose a filter', choices=['alert','trusted','named','other'], default='named')
        parser.add_argument('-n', '--name', type = str, help = 'Searches for name')
        parser.add_argument('-c', '--cameraName', type=str, help='Name of camera in the console')
        parser.add_argument('--csv', type=str, help= 'Name the csv file', default='report')
        parser.add_argument('-r', '--report', type=str, help='Name the folder for csv file and thumbnails', default='Report')

        return parser

    #decrypts the jpg and saves the image to a folder
    def saving_img(self):
        #url of the api
        endpoint = self.thumbnail
        resp = self.media_sess.get(endpoint,
        verify=False)
        content = resp.content
        #opens the folder and writes the image to it
        with open(self.args.report +'/' + self.name + '_' + str(self.count + 1) + '.jpg', 'wb') as f:
            # write the data
            f.write(content)
            f.close()
        self.fileName = (self.args.report +'/' + self.name + '_' + str(self.count + 1) + '.jpg')

    #converts the ms time to a timestamp
    def human_time(self, event):
        event = event/1000
        timestamp = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(event))
        return timestamp

    #converts the timestamp to ms time
    def milliseconds_time(human):
        # converts human time to ms. the +25200000 is to get it to local time and not GMT
        ms_time = (calendar.timegm(time.strptime(human, '%Y-%m-%d~%H:%M:%S')) * 1000) + 25200000
        return ms_time

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

    #gets the camera_name from the uuid
    def camera_name(self, uuid, data_camera):
        for value in data_camera['cameraStates']:
            if uuid == value['uuid']:
                return value['name']

    #uses the api to get the recent faces
    def recent_faces(self):
        # url of the api
        endpoint = self.api_url + "/api/face/getRecentFaceEventsV2"
        #checks to see if the user put in a start and end time if not it defaults to one hour before current
        if self.args.startTime:
            start = self.milliseconds_time(self.args.startTime)
        else:
            start = int(round((time.time() - 3600) * 1000))
        if self.args.endTime:
            end = self.milliseconds_time(self.args.endTime)
        else:
            end = int(round(time.time() * 1000))
        #any parameters
        payload = {
            "filter":{"types":[self.args.filter]}, #arguement to filter alert, trusted, named, or other
            "interval":{
                "end": end,
                "start": start
            }
        }
        resp = self.api_sess.post(endpoint, json=payload,
        verify=False)
        content = resp.content
        data = json.loads(content)
        return data

    #adds the name, timestamp, camera name, and sighting number to a csv
    def csv_add(self, value):
        timestamp = self.human_time(value['eventTimestamp'])
        self.csv_data.append([])
        self.name = value['faceName']
        self.csv_data[self.count].append(self.name)
        self.csv_data[self.count].append(timestamp)
        data_camera = self.camera_data()
        camera = self.camera_name(value['deviceUuid'], data_camera)
        self.csv_data[self.count].append(camera)
        self.thumbnail = self.mediaBaseURL + value['thumbnailS3Key']
        self.saving_img()
        self.csv_data[self.count].append(self.fileName)
        with open(self.args.report + '/' + self.args.csv + '.csv', 'w', newline = '') as f:
            writer = csv.writer(f)     # create the csv writer
            writer.writerow(self.header)    # write the header
            writer.writerows(self.csv_data) # write the data

    def execute(self):
        self.count = 0
        self.mediaBaseURL = "https://media.rhombussystems.com/media/faces?s3ObjectKey="
        self.header = ['Name', 'Date', 'Camera', 'Image File Name']
        self.csv_data = []
        data_recentFaces = self.recent_faces()
        #gets a path and makes a directory file to the path
        path = os.getcwd()
        os.mkdir(path + '/' + self.args.report)
        #checks if there is an arguement for a name to filter and only get instances with them
        if self.args.name:
            final_list = [event for event in data_recentFaces['faceEvents'] if event["faceName"] == self.args.name]
            for value in final_list:
                self.csv_add(value)
                self.count += 1
        #checks for an arguement to filter only certain cameras
        elif self.args.cameraName:
            for value in self.data_camera['cameraStates']:
                if self.args.cameraName == value['name']:
                    uuid = value['uuid']
            final_list = [event for event in data_recentFaces['faceEvents'] if event["deviceUuid"] == uuid]
            for value in final_list:
                self.csv_add(value)
                self.count += 1
        #checks for arguements of both certain cameras and a certain person to filter
        elif self.args.cameraName and self.args.name:
            for value in self.data_camera['cameraStates']:
                if self.args.cameraName == value['name']:
                    uuid = value['uuid']
            initial_list = [event for event in data_recentFaces['faceEvents'] if event["faceName"] == self.args.name]
            final_list = [event for event in initial_list if event["deviceUuid"] == uuid]
            for value in final_list:
                self.csv_add(value)
                self.count += 1
        #if no filter arguements it just grabs all from that time
        else:
            for value in data_recentFaces['faceEvents']:
                self.csv_add(value)
                self.count += 1


if __name__ == "__main__":
    engine = faceProject(sys.argv[1:])
    engine.execute()