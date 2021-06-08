import requests
from datetime import datetime, timedelta
import time
import json
import calendar
import csv
import sys
import os
import argparse

def argparser():
    my_parser = argparse.ArgumentParser()

    #aruements avaiable for the user to customize
    my_parser.add_argument('APIkey', type=str, help='Get this from your console')
    my_parser.add_argument('-s', '--startTime', type=str, help='Add the end search time in yyyy-mm-dd~(0)0:00:00 or default to 1 hour before current time')
    my_parser.add_argument('-e', '--endTime', type=str, help='Add the end search time in yyyy-mm-dd~(0)0:00:00 or default to current time')
    my_parser.add_argument('-f', '--filter', type=str, help= 'Choose a filter', choices=['alert','trusted','named','other'], default='named')
    my_parser.add_argument('-n', '--name', type = str, help = 'Searches for name')
    my_parser.add_argument('-c', '--cameraName', type=str, help='Name of camera in the console')
    my_parser.add_argument('--csv', type=str, help= 'Name the csv file', default='report')
    my_parser.add_argument('-r', '--report', type=str, help='Name the folder for csv file and thumbnails', default='Report')

    args = my_parser.parse_args()
    return args

args = argparser()

#decrypts the jpg and saves the image to a folder
def saving_img(thumbnail, name, count):
    if __name__ == "__main__":
        #url of the api
        endpoint = thumbnail

        api_key = args.APIkey

        sess = requests.session()

        today = datetime.now().replace(microsecond=0, second=0, minute=0)
        end_time = today
        start_time =  (end_time - timedelta(days=365))

        sess.headers = {
            "x-auth-scheme": "api-token",
            "x-auth-apikey": api_key
        }

        resp = sess.get(endpoint,
        verify=False)

        content = resp.content
        #print(resp.status_code)

        #opens the folder and writes the image to it
        with open(args.report +'/' + 'Sighting #' + str(count + 1) + '_' + name + '.jpg', 'wb') as f:
            # write the data
            f.write(content)
            f.close()

#converts the ms time to a timestamp
def human_time(event):
    event = event/1000
    timestamp = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(event))
    return timestamp

#converts the timestamp to ms time
def milliseconds_time(human):
    # converts human time to ms. the +25200000 is to get it to local time and not GMT
    ms_time = (calendar.timegm(time.strptime(human, '%Y-%m-%d~%H:%M:%S')) * 1000) + 25200000
    return ms_time

#gets the api data about the cameras in the console and returns it
def camera_data():
    if __name__ == "__main__":
        # url of the api
        endpoint = "https://api2.rhombussystems.com/api/camera/getMinimalCameraStateList"
        api_key = args.APIkey
        sess = requests.session()
        today = datetime.now().replace(microsecond=0, second=0, minute=0)
        end_time = today
        start_time =  (end_time - timedelta(days=365))
        # any parameters
        payload = {
        }
        sess.headers = {
            "x-auth-scheme": "api-token",
            "x-auth-apikey": api_key
        }
        resp = sess.post(endpoint, json=payload,
        verify=False)
        content = resp.content
        data = json.loads(content)
        return data

#gets the camera_name from the uuid
def camera_name(uuid, data):
    for value in data['cameraStates']:
        if uuid == value['uuid']:
            return value['name']

#uses the api to get the recent faces
def recent_faces():
    if __name__ == "__main__":
        # url of the api
        endpoint = "https://api2.rhombussystems.com/api/face/getRecentFaceEventsV2"
        api_key = args.APIkey
        sess = requests.session()
        today = datetime.now().replace(microsecond=0, second=0, minute=0)
        end_time = today
        start_time =  (end_time - timedelta(days=365))
        #checks to see if the user put in a start and end time if not it defaults to one hour before current
        if args.startTime:
            start = milliseconds_time(args.startTime)
        else:
            start = int(round((time.time() - 3600) * 1000))
        if args.endTime:
            end = milliseconds_time(args.endTime)
        else:
            end = int(round(time.time() * 1000))
        #any parameters
        payload = {
            "filter":{"types":[args.filter]}, #arguement to filter alert, trusted, named, or other
            "interval":{
                "end": end,
                "start": start
            }
        }
        print(payload)
        sess.headers = {
            "x-auth-scheme": "api-token",
            "x-auth-apikey": api_key
        }
        resp = sess.post(endpoint, json=payload,
        verify=False)
        content = resp.content
        data = json.loads(content)
        #print(resp.status_code)
        return data

#adds the name, timestamp, camera name, and sighting number to a csv
def csv_add(value, csv_data, count, data_camera, baseURL, header):
    timestamp = human_time(value['eventTimestamp'])
    csv_data.append([])
    name = value['faceName']
    csv_data[count].append(name)
    csv_data[count].append(timestamp)
    camera = camera_name(value['deviceUuid'], data_camera)
    csv_data[count].append(camera)
    thumbnail = baseURL + value['thumbnailS3Key']
    saving_img(thumbnail, name, count)
    csv_data[count].append(count + 1)
    with open(args.report + '/' + args.csv + '.csv', 'w', newline = '') as f:
        writer = csv.writer(f)     # create the csv writer
        writer.writerow(header)    # write the header
        writer.writerows(csv_data) # write the data

def csv_work(data_recentFaces):
    count = 0
    baseURL = "https://media.rhombussystems.com/media/faces?s3ObjectKey="
    header = ['Name', 'Date', 'Camera', 'Sighting']
    csv_data = []
    data_camera = camera_data()
    #gets a path and makes a directory file to the path
    path = os.getcwd()
    os.mkdir(path + '/' + args.report)
    #checks if there is an arguement for a name to filter and only get instances with them
    if args.name:
        final_list = [event for event in data_recentFaces['faceEvents'] if event["faceName"] == args.name]
        for value in final_list:
            csv_add(value, csv_data, count, data_camera, baseURL, header)
            count += 1
    #checks for an arguement to filter only certain cameras
    elif args.cameraName:
        for value in data_camera['cameraStates']:
            if args.cameraName == value['name']:
                uuid = value['uuid']
        final_list = [event for event in data_recentFaces['faceEvents'] if event["deviceUuid"] == uuid]
        for value in final_list:
            csv_add(value, csv_data, count, data_camera, baseURL, header)
            count += 1
    #checks for arguements of both certain cameras and a certain person to filter
    elif args.cameraName and args.name:
        for value in data_camera['cameraStates']:
            if args.cameraName == value['name']:
                uuid = value['uuid']
        initial_list = [event for event in data_recentFaces['faceEvents'] if event["faceName"] == args.name]
        final_list = [event for event in initial_list if event["deviceUuid"] == uuid]
        for value in final_list:
            csv_add(value, csv_data, count, data_camera, baseURL, header)
            count += 1
    #if no filter arguements it just grabs all from that time
    else:
        for value in data_recentFaces['faceEvents']:
            csv_add(value, csv_data, count, data_camera, baseURL, header)
            count += 1

def main():
    data_recentFaces = recent_faces()
    csv_work(data_recentFaces)

main()