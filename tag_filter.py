import requests
from datetime import datetime, timedelta
import time
import json
import calendar
import csv
import sys
import argparse
import urllib3

# to disable warnings for not verifying host
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class tag_filter:
    def __init__(self, cli_args):
        arg_parser = self.__initialize_argument_parser()
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
            "x-auth-apikey": self.args.APIkey
        }
        today = datetime.now().replace(microsecond=0, second=0, minute=0)
        self.end_time = today
        self.start_time = (self.end_time - timedelta(days=365))

    @staticmethod
    def __initialize_argument_parser():
        parser = argparse.ArgumentParser(
            description = "Filters through tag movements and creates CSV file."
        )

        # arguments available for the user to customize
        parser.add_argument('APIkey', type = str, help = "Your API Key")
        parser.add_argument('name', type = str, help = 'Name of the Tag')
        parser.add_argument('-c', '--csv', type = str, help = "Name of CSV File", default = 'tags')
        parser.add_argument('-m', '--movement', type = str, help = 'Filter by the Type of Movement')
        parser.add_argument('-l', '--limit', type = int, help = "Limit the number of movements tallied")
        parser.add_argument('-s', '--startTime', type = str, help = 'The time at which you want to begin yyyy-mm-dd (0)0:00:00')
        parser.add_argument('-e', '--endTime', type = str, help = "The time at which you want to end yyyy-mm-dd (0)0:00:00")
        
        return parser

    # converts the timestamp to ms time
    def milliseconds_time(self, human):
        # the +25200000 is to produce local time and not GMT
        ms_time = (calendar.timegm(time.strptime(human, '%Y-%m-%d %H:%M:%S')) * 1000) + 25200000
        return ms_time 

    # converts the ms time to timestamp
    def human_time(self, event):
        event = event/1000
        timestamp = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(event))
        return timestamp

    # converts the tag uuid to tag name
    def tag_uuid_convert(self, uuid, tag_name_data):  
        for value in tag_name_data['proximityStates']:
            if uuid == value['tagUuid']:
                return value['name']

    # converts the tag name to tag uuid
    def tag_name_convert(self):    
        for value in self.tag_name_data['proximityStates']:
            if self.args.name == value['name']:
                return value['tagUuid']

    # returns data with device uuid and device name
    def tag_name(self): 
            endpoint = self.api_url + '/api/proximity/getMinimalProximityStateList'
            payload = {
            }
            resp = self.api_sess.post(endpoint, json=payload,
                            verify=False)
            order_content = resp.content.decode('utf8')
            tag_name_data = json.loads(order_content)
            return tag_name_data

    # returns data with address
    def locations(self):
        endpoint = self.api_url + "/api/location/getLocations"
        payload = {
        }
        resp = self.api_sess.post(endpoint, json=payload,
                       verify=False)
        order_content = resp.content.decode('utf8')
        # Load the JSON to a Python list & dump it back out as formatted JSON
        location_data = json.loads(order_content)
        return location_data

    # converts lat and lon to street address
    def location_data_print(self, location_data, lat_1):
        for value in location_data['locations']:
            lat_2 = round(value['latitude'], 2)
            if lat_1 == lat_2:
                address = value['address1'] + ' ' + value['address2']
                return address

    def tag_data(self):    # returns data that should be put in CSV file
        endpoint = self.api_url + "/api/proximity/getLocomotionEventsForTag"
        self.tag_name_data = self.tag_name()
        self.uuid = self.tag_name_convert()

        if self.args.startTime:
            self.start_time = self.milliseconds_time(self.args.startTime)
        else:
            self.start_time = int(round((time.time() - (3600 * 24)) * 1000))  # start time defaults to 24 hours ago
        if self.args.endTime:
            self.end_time = self.milliseconds_time(self.args.endTime)
        else:
            self.end_time = int(round(time.time() * 1000))    # end time defaults to now

        payload = {
            "movementFilter": self.args.movement,
            "tagUuid": self.uuid,
            "createdBeforeMs": self.end_time,
            "createdAfterMs": self.start_time
        }
        resp = self.api_sess.post(endpoint, json=payload,
                        verify=False)
        order_content = resp.content.decode('utf8')
        data = json.loads(order_content)
        return data

    def csv_add(self, value):
        self.csv_data.append([])
        self.real_name = self.tag_uuid_convert(value['tagUuid'], self.tag_name_data)
        self.csv_data[self.count].append(self.real_name)
        lat_1 = round(value['gpsLocation']['lat'], 2)
        address = self.location_data_print(self.location_data, lat_1)
        self.csv_data[self.count].append(address)
        self.csv_data[self.count].append(value['movement'])
        self.csv_data[self.count].append(self.human_time(value['timestampMs']))
        self.csv_data[self.count].append(self.count + 1)
   
        with open(self.args.csv + '.csv', 'w', newline = '', encoding='UTF8') as f:
            writer = csv.writer(f)    # create the csv writer
            writer.writerow(self.header)    # write the header
            writer.writerows(self.csv_data) # write the data

    def execute(self):
        self.header = ['Tag Name', 'Address', 'Movement', 'Date', 'Movement']
        self.csv_data =[]
        self.data = self.tag_data()  
        self.tag_name_data = self.tag_name()    
        self.location_data = self.locations()
        self.count = 0
        self.final_list = []

        for event in self.data['locomotionEvents']:
            real_uuid = self.tag_name_convert()
            if self.args.name and not event['tagUuid'] == real_uuid:
                continue
            if self.args.movement and not event['movement'] == self.args.movement:
                continue
            # ...
            self.final_list.append(event)

        if self.args.limit:
            for event in self.final_list:
                self.csv_add(event)
                self.count += 1
                if self.count == self.args.limit:
                    break
        else:
            for event in self.final_list:
                self.csv_add(event)
                self.count += 1

if __name__ == "__main__":
    engine = tag_filter(sys.argv[1:])
    engine.execute()