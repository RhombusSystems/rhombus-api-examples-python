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

class licensePlateProject:
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

        self.media_sess = requests.session()
        self.media_sess.headers = {
            "Accept": "application/json",
            "x-auth-scheme": "api-token",
            "Content-Type": "application/json",
            "x-auth-apikey": self.args.APIkey}

    @staticmethod
    def __initalize_argument_parser():
        parser = argparse.ArgumentParser(
            description= "Gets a report of the recent faces and downloads the pictures of each face.")
        #aruements avaiable for the user to customize
        parser.add_argument('APIkey', type=str, help='Get this from your console')
        parser.add_argument('cameraName', type=str, help='Name of camera in the console')
        parser.add_argument('-s', '--startTime', type=str, help='Add the end search time in yyyy-mm-dd~(0)0:00:00 or default to 1 hour before current time')
        parser.add_argument('-e', '--endTime', type=str, help='Add the end search time in yyyy-mm-dd~(0)0:00:00 or default to current time')
        parser.add_argument('-f', '--filter', type=str, help= 'Choose a filter', choices=['alert','trusted','named','other'], default='other')
        parser.add_argument('-l', '--licenseplate', type = str, help = 'Searches for a license')
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
        self.fileName = (self.name + '_' + str(self.count + 1) + '.jpg')

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

    #gets the camera_name from the uuid
    def camera_uuid(self, data_camera):
        self.cameraUuids = []
        for value in data_camera['cameraStates']:
            for event in self.camera_list:
                if event == value['name']:
                    self.cameraUuids.append(value['uuid'])
        
    #converts the ms time to a timestamp
    def human_time(self, event):
        event = event/1000
        timestamp = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(event))
        return timestamp

    #converts the timestamp to ms time
    def milliseconds_time(self, human):
        # converts human time to ms. the +25200000 is to get it to local time and not GMT
        ms_time = (calendar.timegm(time.strptime(human, '%Y-%m-%d~%H:%M:%S')) * 1000) + 25200000
        return ms_time

    def namesCamera(self):
        self.args.cameraName = self.args.cameraName.replace(", ", ",")
        self.camera_list = self.args.cameraName.split(",")

    def recentVehicle(self):
        # url of the api
        endpoint = self.api_url + "/api/vehicle/getRecentVehicleEvents"
        #checks to see if the user put in a start and end time if not it defaults to one hour before current
        if self.args.startTime:
            start = self.milliseconds_time(self.args.startTime)
        else:
            start = int(round((time.time() - 1800) * 1000))
        if self.args.endTime:
            end = self.milliseconds_time(self.args.endTime)
        else:
            end = int(round(time.time() * 1000))
        # any parameters
        payload = {
            'deviceUuids': self.cameraUuids,
            "filterTypes": [self.args.filter],
            "endTimeMs": end,
            "startTimeMs": start
        }
        resp = self.api_sess.post(endpoint, json=payload,
        verify=False)
        content = resp.content
        data = json.loads(content)
        organized = json.dumps(resp.json(), indent=2, sort_keys=True)
        return data

    #adds the name, timestamp, camera name, and sighting number to a csv
    def csv_add(self, value, data_camera):
        timestamp = self.human_time(value['eventTimestamp'])
        self.csv_data.append([])
        if value['name'] == None:
            self.name = 'Unidentified'
        else:
            self.name = value['name']
        self.csv_data[self.count].append(self.name)
        self.csv_data[self.count].append(value['vehicleLicensePlate'])
        self.csv_data[self.count].append(timestamp)
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
        self.header = ['Vehicle', 'LicensePlate', 'Date', 'Camera', 'Image File Name']
        self.csv_data = []
        data_camera = self.camera_data()
        self.namesCamera()
        self.camera_uuid(data_camera)
        data_recentVehicle = self.recentVehicle()
        #gets a path and makes a directory file to the path
        path = os.getcwd()
        os.mkdir(path + '/' + self.args.report)
        if self.args.licenseplate:
            final_list = [event for event in data_recentVehicle['events'] if self.args.licenseplate == event['vehicleLicensePlate']]
            for value in final_list:
                self.csv_add(value, data_camera)
                self.count += 1
        else: 
            for value in data_recentVehicle['events']:
                self.csv_add(value, data_camera)
                self.count += 1

if __name__ == "__main__":
    engine = licensePlateProject(sys.argv[1:])
    engine.execute()