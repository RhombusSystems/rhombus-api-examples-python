import requests
from datetime import datetime, timedelta
import time
import json
import calendar
import csv
import sys
import argparse
import urllib3
import os

# to disable warnings for not verifying host
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class tag_stats:
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
            "x-auth-apikey": self.args.APIkey}

        today = datetime.now().replace(microsecond=0, second=0, minute=0)
        self.end_time = today
        self.start_time = (self.end_time - timedelta(days=365))

    @staticmethod
    def __initialize_argument_parser():
        parser = argparse.ArgumentParser(
            description = "Returns statistics on tag arrvials and departures."
        )
        
        # arguments available for the user to customize
        parser.add_argument("APIkey", type = str, help = 'Your API key')
        parser.add_argument("name", type = str, help = 'Name of the tag')
        parser.add_argument('-s', "--startTime", type = str, help = 'Start time of data collection yyyy-mm-dd (0)0:00:00')
        parser.add_argument('-e', '--endTime', type = str, help = 'End time of data collection yyyy-mm-dd (0)0:00:00')
        parser.add_argument('-c', '--csv', type = str, help = 'Name the CSV file', default = "tagstats")
        parser.add_argument('-t', '--text', type = str, help = 'Name of the text file', default = 'tagstats')
        parser.add_argument('-r', '--report', type = str, help = "Name of the folder", default = 'tagstats_report')
        
        return parser

    # converts the ms time to timestamp
    def human_time(self, event):
        event = event/1000
        timestamp = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(event))
        return timestamp

    # converts human time to milliseconds  
    def milliseconds_time(self, human):
        # the +25200000 is to get it to local time and not GMT
        ms_time = (calendar.timegm(time.strptime(human, '%Y-%m-%d %H:%M:%S')) * 1000) + 25200000
        return ms_time 

    # opens the folder that the two files will go into
    def folder_open(self):
        path = os.getcwd()
        os.mkdir(path + '/' + self.args.report)

    # Get seconds from HH:MM:SS
    def get_sec(self, time_str):   # https://stackoverflow.com/questions/6402812/how-to-convert-an-hmmss-time-string-to-seconds-in-python 
        h, m, s = time_str.split(':')
        return int(h) * 3600 + int(m) * 60 + int(s) 

    # converts the tag name to tag uuid
    def tag_name_convert(self):    
        for value in self.tag_name_data['proximityStates']:
            if self.args.name == value['name']:
                return value['tagUuid']

    # calculates the averages of seconds
    def avg_calc(self, some_list, count):
        self.total_seconds = 0
        for value in some_list:
            self.total_seconds += int(self.get_sec(value))
            count += 1

        if count == 0:
            print("There are no arrival or departure times during this time period.")
            return
        else:
            avg_seconds = self.total_seconds / count
            return avg_seconds

    # Get HH:MM:SS from seconds 
    def get_time(self, seconds):    # accurate to the second, could be one low (but not over)
        hours = int(seconds) / 60 / 60 
        real_hours = int(hours)
        minutes = (hours - int(hours)) * 60
        real_minutes = int(minutes)
        seconds = (minutes - int(minutes)) * 60
        seconds = seconds = int(seconds)
        real_seconds = int(seconds) 
        time = str(str(real_hours) + ":" + str(real_minutes) + ":" + str(real_seconds))
        return time
    
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

    def get_tag_times(self):
        endpoint = self.api_url + "/api/proximity/getLocomotionEventsForTag"
        self.tag_name_data = self.tag_name()
        self.tag_uuid = self.tag_name_convert()
        if self.args.startTime:
            self.start_time = self.milliseconds_time(self.args.startTime)
        else:
            self.start_time = int(round((time.time() - (3600 * 192)) * 1000))  # start time defaults to 8 days ago to accomodate my week data set
        if self.args.endTime:
            self.end_time = self.milliseconds_time(self.args.endTime)
        else:
            self.end_time = int(round(time.time() * 1000))    # end time defaults to now

        payload = {
            "createdAfterMs": self.start_time,
            "createdBeforeMs": self.end_time,
            "tagUuid": self.tag_uuid
        }

        resp = self.api_sess.post(endpoint, json=payload,
                        verify=False)

        order_content = resp.content.decode('utf8')
        # Load the JSON to a Python list & dump it back out as formatted JSON
        data = json.loads(order_content)
        return data

    def data_csv_collect(self):
        self.data = self.get_tag_times()
        small_list = []
        big_list = []

        for value in self.data['locomotionEvents']:
            if value['movement'] == 'ARRIVAL' or value['movement'] == "DEPARTURE":
                # arrive_time = value['timestampMs']
                time = self.human_time(value['timestampMs'])
                small_list = []
                small_list.append(value['movement'])   # have to create function for these two parts
                small_list.append(time)
                big_list.append(small_list)

        return big_list

    def execute(self):
        self.data = self.get_tag_times()
        arrival_times = []     # empty list of arrvial times
        departure_times = []   # empty list of departure times
        milli_list = []        # empty list of all the times in milliseconds - used for comparison of days
        time_list = []         # empty list of all the times in timestamps - used for comparison of days
        duration_times = []    # empty list of the duration times 
        i = 0                  # counter 

        # tag name input validation
        if 'locomotionEvents' not in self.data:
            print("Tag name does not exist within organizaton.")
            return 

        for value in self.data['locomotionEvents']:
            if value['movement'] == 'ARRIVAL':
                time = self.human_time(value['timestampMs'])
                arrival_times.append(time[17:])
                milli_list.append(value['timestampMs'])
            elif value['movement'] == 'DEPARTURE':
                time = self.human_time(value['timestampMs'])
                departure_times.append(time[17:]) 
                milli_list.append(value['timestampMs'])

        for value in milli_list:
            date = datetime.fromtimestamp(value/1000.0)
            day_num = date.strftime("%d")
            time_list.append(day_num)

        while i < (len(time_list) - 1):
            # Arrivals and departures will be next to each other in the data 
            if time_list[i] == time_list[i + 1]:
                duration_secs = (int(milli_list[i]) - int(milli_list[i+1])) / 1000
                duration_time = self.get_time(duration_secs)
                duration_times.append(duration_time)
                i += 1
            else:
                i += 1
        
        arrival_times.sort()
        departure_times.sort() 
        duration_times.sort()

        self.total_seconds = 0
        count_1 = 0
        count_2 = 0
        count_3 = 0

        self.folder_open()
        
        arrive_avg_seconds = self.avg_calc(arrival_times, count_1)
        depart_avg_seconds = self.avg_calc(departure_times, count_2)
        duration_avg_seconds = self.avg_calc(duration_times, count_3)
        
        file = open(self.args.report + '/' + self.args.text + '.txt', 'w')
        # arrival_times = [... ... ...]
        file.write("--Arrival Times-- \n")
        file.write("Earliest Arrival: {}\n".format(arrival_times[0]))
        file.write("Latest Arrial: {}\n".format(arrival_times[-1]))
        file.write("Average Arrival Time: {}\n".format(self.get_time(arrive_avg_seconds)))
    
        file.write("\n--Departure Times-- \n")
        file.write("Earliest Departure: {}\n".format(departure_times[0]))
        file.write("Latest Departure: {}\n".format(departure_times[-1]))
        file.write("Average Departure Time: {}\n".format(self.get_time(depart_avg_seconds)))

        file.write("\n--Duration Times-- \n")
        file.write("Shortest Duration: {}\n".format(duration_times[0]))
        file.write("Longest Duration: {}\n".format(duration_times[-1]))
        file.write("Average Duration Time: {}\n".format(self.get_time(duration_avg_seconds)))

        header = ['Movement', 'Date']
        big_list = self.data_csv_collect()

        with open(self.args.report + '/' + self.args.csv + '.csv', 'w', newline = '', encoding='UTF8') as f:
            writer = csv.writer(f)         # create the csv writer
            writer.writerow(header)        # write the header
            writer.writerows(big_list)     # write the data   
   
if __name__ == "__main__":
    engine = tag_stats(sys.argv[1:])   
    engine.execute()
