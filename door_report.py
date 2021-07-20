import sys
import csv
import time
import json
import urllib3 
import requests
import argparse
import calendar
from datetime import datetime, timedelta

# to disable warnings for not verifying host
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class doorReport:
    def __init__(self, cli_args):
        # initializes argument parser
        arg_parser = self.__initialize_argument_parser()
        self.args = arg_parser.parse_args(cli_args)
        self.api_url = "https://api2.rhombussystems.com"
        # starts one API session that is used by all requests
        self.api_sess = requests.session()
        self.api_sess.headers = {
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
            description = "Gets a report of the recent door openings and closings."
        )

        # command line arguments for the user
        parser.add_argument("APIkey", type=str, help="Get this from your console.s")
        parser.add_argument("sensorName", type=str, help='Name of sensor for which information will be collected.')
        parser.add_argument("-s", "--startTime", type=str, help="Start time of data collection yyyy-mm-dd (0)0:00:00")
        parser.add_argument("-e", "--endTime", type=str, help="End time of data collection yyyy-mm-dd (0)0:00:00")
        parser.add_argument("-f", "--filter", type = str, help = "Filter for data collection", default = None, choices = ['OPEN', 'CLOSED', 'AJAR'])   
        parser.add_argument('-c', '--csv', type = str, help = "Name of CSV File", default = 'doors')
        return parser

    # converts sensor name to uuid
    def name_convert_uuid(self):
        for value in self.name_data['doorStates']:
            if self.args.sensorName == value['name']:
                uuid = (value['sensorUuid'])
                return uuid

    # converts the timestamp to ms time
    def milliseconds_time(self, human):
        # the +25200000 is to produce local time and not GMT
        ms_time = (calendar.timegm(time.strptime(human, '%Y-%m-%d %H:%M:%S')) * 1000) + 25200000
        return ms_time 

    # converts the millisecond time to timestamp
    def human_time(self, event):
        event = event/1000
        timestamp = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(event))
        return timestamp

    # converts location uuid to an address
    def uuid_convert_address(self):
        for value in self.location_data['locations']:
            if value['uuid'] == self.uuid:
                address = value['address1'] + ' ' + value['address2']
                return address

    # creates list of lists that will be used in CSV creation
    def list_create(self, event):
        small_list = []
        small_list.append(self.args.sensorName)
        self.uuid = event['locationUuid']  
        address = self.uuid_convert_address()
        small_list.append(address)
        small_list.append(event['state'])
        small_list.append(self.human_time(event['timestampMs']))
        small_list.append(self.real_count)
        # adding the small list to the big list, will end with list of lists
        self.big_list.append(small_list)

    # returns data with address
    def locations(self):
        endpoint = self.api_url + "/api/location/getLocations"
        payload = {
        }
        resp = self.api_sess.post(endpoint, json=payload,
                       verify=False)
        content = resp.content
        # Load the JSON to a Python list & dump it back out as formatted JSON
        location_data = json.loads(content)
        return location_data

    # returns data with door sensor name and uuid
    def door_name_data(self):
        endpoint = self.api_url + "/api/door/getMinimalDoorStateList"
        payload = {}
        resp = self.api_sess.post(endpoint, json=payload,
        verify=False)
        content = resp.content
        door_name_data = json.loads(content)
        return door_name_data

    # returns general data
    def door_events(self):
        self.name_data = self.door_name_data()
        self.uuid = self.name_convert_uuid()
        endpoint = self.api_url + "/api/door/getDoorEventsForSensor"

        if self.args.startTime:
            self.start_time = self.milliseconds_time(self.args.startTime)
        else:
            self.start_time = int(round((time.time() - (3600 * 24)) * 1000))  # with no argument, start time defaults to 24 hours ago
        if self.args.endTime:
            self.end_time = self.milliseconds_time(self.args.endTime)
        else:
            self.end_time = int(round(time.time() * 1000))    # with no argument, end time defaults to now

        payload = {
            "createdBeforeMs": self.end_time,
            "createdAfterMs": self.start_time,
            "sensorUuid": self.uuid,
            "stateFilter": self.args.filter
        }
        resp = self.api_sess.post(endpoint, json=payload,
        verify=False)
        content = resp.content
        events_data = json.loads(content)
        return events_data

    def execute(self):
        self.big_list = []    # list of lists 
        count = 0             # count of all events 
        self.real_count = 0   # count of non-redundant events
        self.header = ['Sensor Name', 'Address', 'Status', 'Date', 'Event Number']   # headers for the CSV file

        events_data = self.door_events()
        self.location_data = self.locations()

        if 'doorEvents' not in events_data:  # input validation for sensor name
            print("No data for given parameters.")
            return 

        for event in events_data['doorEvents']:
            count += 1    # adding to total event count
            if self.args.filter:
                # if the user has entered a filter, then the events would all be the same 
                # Therefore, we do not need to check for redundancy
                self.list_create(event)
            else:
                if event['stateChanged'] == True:   # Do not include redundant events
                    self.list_create(event)
                    self.real_count += 1    # count of events that will actually be included
                else:
                    pass

        if self.big_list == []:
            # input must have been invalid if there were no data generated
            print("No data generated.")
            print("Make sure that data are available within the specified parameters.")

        # verifying the name of the CSV file
        if '.csv' in self.args.csv:
            self.CSV = self.args.csv
        else:
            self.CSV = self.args.csv + '.csv'

        # once list of lists has been compiled, create the CSV file 
        with open(self.CSV, 'w', newline = '', encoding='UTF8') as f:
            writer = csv.writer(f)              # create the csv writer
            writer.writerow(self.header)        # write the header
            writer.writerows(self.big_list)     # write the data

if __name__ == "__main__":
    engine = doorReport(sys.argv[1:])
    engine.execute()
