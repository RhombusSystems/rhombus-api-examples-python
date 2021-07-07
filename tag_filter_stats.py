import os
import csv
import sys
import time
import json
import urllib3
import requests
import argparse
import calendar
from datetime import datetime, timedelta

# to disable warnings for not verifying host
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class TagFilter:
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
            description = "Filters through tag movements and creates CSV file."
        )
        # command line arguments for the user
        parser.add_argument('APIkey', type = str, help = "Your API Key")
        parser.add_argument('name', type = str, help = 'Name of the Tag')
        parser.add_argument('-c', '--csv', type = str, help = "Name of CSV File", default = 'tags')
        parser.add_argument('-m', '--movement', type = str, help = 'Filter by the Type of Movement', default = None, 
                            choices = ["ARRIVAL", "DEPARTURE", "MOVED_SIGNIFICANTLY", "UNKNOWN"])
        parser.add_argument('-l', '--limit', type = int, help = "Limit the number of movements tallied")
        parser.add_argument('-s', '--startTime', type = str, help = 'Start time fo data collection yyyy-mm-dd (0)0:00:00')
        parser.add_argument('-e', '--endTime', type = str, help = "End time of data collection yyyy-mm-dd (0)0:00:00")
        parser.add_argument("--stats", type = bool, help = "Receive statistics (True / False)")
        parser.add_argument('-t', '--text', type = str, help = 'Name of the text file', default = 'tagstats')
        parser.add_argument('-r', '--report', type = str, help = "Name of the folder", default = 'tagstats_report')
        return parser

    # opens folder for files 
    def folder_open(self):
        path = os.getcwd()
        os.mkdir(path + '/' + self.args.report)

    # gets seconds from HH:MM:SS
    def get_sec(self, time_str): 
        h, m, s = time_str.split(':')
        return int(h) * 3600 + int(m) * 60 + int(s)

    # returns unique values of a list
    def unique(self, list):
        unique_lst = []
        for value in list:
            if value not in unique_lst:
                unique_lst.append(value)
        return unique_lst

    # converts the timestamp to millisecond time
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
    
    # converts the location uuid to an address
    def uuid_convert_address(self):
        for value in self.location_data['locations']:
            if value['uuid'] == self.loc_uuid:
                address = value['address1'] + " " + value['address2']
                return address

    # returns data with tag uuid and tag name
    def tag_name(self): 
            endpoint = self.api_url + '/api/proximity/getMinimalProximityStateList'
            payload = {
            }
            resp = self.api_sess.post(endpoint, json=payload,
            verify=False)
            content = resp.content
            tag_name_data = json.loads(content)
            return tag_name_data

    # calculates the averages of seconds
    def avg_calc(self, some_list, count):
        self.total_seconds = 0
        for value in some_list:
            self.total_seconds += int(self.get_sec(value))
            count += 1
        # no events if count equals 0
        if count == 0:  
            print("There are no arrival or departure times during this time period.")
            return
        else:
            avg_seconds = self.total_seconds / count
            return avg_seconds

    # Get HH:MM:SS from seconds 
    def get_time(self, seconds):   
        hours = int(seconds) / 60 / 60           # convert total seconds to hours (float)
        real_hours = int(hours)                  # rounds the hours
        minutes = (hours - int(hours)) * 60      # converts partial hour into minutes (float)
        real_minutes = int(minutes)              # rounds the minutes
        seconds = (minutes - int(minutes)) * 60  # converts partial minute into seconds (float)
        seconds = seconds = int(seconds)         
        real_seconds = int(seconds)              # rounds the seconds
        time = str(str(real_hours) + ":" + str(real_minutes) + ":" + str(real_seconds))  # creates timestamp
        return time

    # returns data with address
    def locations(self):
        endpoint = self.api_url + "/api/location/getLocations"
        payload = {
        }
        resp = self.api_sess.post(endpoint, json=payload,
                       verify=False)
        content = resp.content
        location_data = json.loads(content)
        return location_data

    # returns data that is included in CSV file
    def tag_data(self):   
        endpoint = self.api_url + "/api/proximity/getLocomotionEventsForTag"
        self.tag_name_data = self.tag_name()
        # uuid will be used in the payload
        self.uuid = self.tag_name_convert()

        if self.args.startTime:
            self.start_time = self.milliseconds_time(self.args.startTime)     # converts timestamp argument to milliseconds
        else:
            self.start_time = int(round((time.time() - (3600 * 240)) * 1000)) # start time defaults to 10 days ago
        if self.args.endTime:
            self.end_time = self.milliseconds_time(self.args.endTime)         # converts timestamp argument to milliseconds
        else:
            self.end_time = int(round(time.time() * 1000))                    # end time defaults to now

        payload = {
            "movementFilter": self.args.movement,
            "tagUuid": self.uuid,
            "createdBeforeMs": self.end_time,
            "createdAfterMs": self.start_time
        }
        resp = self.api_sess.post(endpoint, json=payload,
                        verify=False)
        content = resp.content
        data = json.loads(content)
        return data

    def execute(self):
        self.header = ['Tag Name', 'Address', 'Movement', 'Date', 'Movement']  # header for CSV file

        self.data = self.tag_data()  
        self.tag_name_data = self.tag_name()    
        self.location_data = self.locations()

        arrival_times = []     # empty list of arrvial times
        departure_times = []   # empty list of departure times
        milli_list = []        # empty list of all the times in milliseconds - used for comparison of days
        time_list = []         # empty list of all the times in timestamps - used for comparison of days
        duration_times = []    # empty list of the duration times 
        i = 0                  # counter for averaging statistics 

        self.count = 0    # this will be a count of total events
        big_list = []     # big list that will contain smaller lists of events (list of lists)

        if 'locomotionEvents' not in self.data:     # input validation for sensor name
            print("Tag name does not exist within organizaton.")
            return 

        self.folder_open()  # opens folder for CSV and text files 

        if self.args.stats == True:
            # only write text file if option was chosen by the user
            for value in self.data['locomotionEvents']:
                if value['movement'] == 'ARRIVAL':
                    time = self.human_time(value['timestampMs']) # creating timestamp
                    arrival_times.append(time[17:])              # appending timestamp to list of timestamps 
                    milli_list.append(value['timestampMs'])      # appending ms time to list of ms times

                elif value['movement'] == 'DEPARTURE':
                    time = self.human_time(value['timestampMs']) # creating timestamp
                    departure_times.append(time[17:])            # appending timestamp to list of timestamps
                    milli_list.append(value['timestampMs'])      # appending ms time to list of ms times

            for value in milli_list:
                date = datetime.fromtimestamp(value/1000.0)  # creating a date from ms time
                day_num = date.strftime("%d")   # "day_num" is the actual number of the day in the month
                time_list.append(day_num)       # that number is appended to a list

            while i < (len(time_list) - 1): # goes through list of day numbers 
                # Arrivals and departures will be next to each other in the data 
                if time_list[i] == time_list[i + 1]:  # if two times are from the same day
                    # difference in sec from start time to end time
                    duration_secs = (int(milli_list[i]) - int(milli_list[i+1])) / 1000 
                    # converting seconds to timestamp
                    duration_time = self.get_time(duration_secs) 
                    duration_times.append(duration_time)  # appending timestamp
                    i += 1
                else:
                    i += 1

            # sorting the times in the lists
            arrival_times.sort()
            departure_times.sort() 
            duration_times.sort()

            self.total_seconds = 0

            # creating three seperate counts
            count_1 = 0
            count_2 = 0
            count_3 = 0

            # the average seconds for arrivals, departues, and duration
            arrive_avg_seconds = self.avg_calc(arrival_times, count_1)
            depart_avg_seconds = self.avg_calc(departure_times, count_2)
            duration_avg_seconds = self.avg_calc(duration_times, count_3)

            # opening the text file
            file = open(self.args.report + '/' + self.args.text + '.txt', 'w')  
            # writing to the text file 
            file.write("--Arrival Times-- \n")
            file.write("Earliest Arrival: {}\n".format(arrival_times[0]))  # first time in the list of arrivals
            file.write("Latest Arrial: {}\n".format(arrival_times[-1]))    # last time in the list of arrivals
            file.write("Average Arrival Time: {}\n".format(self.get_time(arrive_avg_seconds))) # timestamp of average arrival time

            file.write("\n--Departure Times-- \n")
            file.write("Earliest Departure: {}\n".format(departure_times[0]))  # first time in the list of departures
            file.write("Latest Departure: {}\n".format(departure_times[-1]))   # last time in the list of departures
            file.write("Average Departure Time: {}\n".format(self.get_time(depart_avg_seconds))) # timestamp of average departure time

            file.write("\n--Duration Times-- \n")
            file.write("Shortest Duration: {}\n".format(duration_times[0]))   # first HH:MM:SS in list of duration times
            file.write("Longest Duration: {}\n".format(duration_times[-1]))   # second HH:MM:SS in list of duration times
            file.write("Average Duration Time: {}\n".format(self.get_time(duration_avg_seconds))) # timestamp of average duration time 
        
        for event in self.data['locomotionEvents']: 
            small_list = []  # creating an empty "small list" each time 
            real_uuid = self.tag_name_convert() 

            # input validation for command line arguments
            if self.args.name and not event['tagUuid'] == real_uuid:
                continue
            if self.args.movement and not event['movement'] == self.args.movement:
                continue

            # setting up info to add
            self.real_name = self.tag_uuid_convert(event['tagUuid'], self.tag_name_data)
            self.loc_uuid = event["locationUuid"]
            address = self.uuid_convert_address()
            
            # adding info to "small list"
            small_list.append(self.real_name)                           # name of tag
            small_list.append(address)                                  # address
            small_list.append(event['movement'])                        # movement type
            small_list.append(self.human_time(event['timestampMs']))    # timestamp of movement 
            small_list.append(self.count + 1)                           # count of events
            self.count += 1 
            # append the small list to a big list (list of lists)
            big_list.append(small_list) 

        if big_list == []:
            # input was invalid if no data were genreated
            if self.args.movement:
                print("No data generated.")
                print("Make sure that data are available within the specified parameters.")

        # verifying the name of the CSV file
        if '.csv' in self.args.csv:
            self.CSV = self.args.csv
        else:
            self.CSV = self.args.csv + '.csv'

        # once list of lists has been compiled, create the CSV file 
        with open(self.args.report + '/' + self.CSV, 'w', newline = '', encoding='UTF8') as f:
            writer = csv.writer(f)          # create the csv writer
            writer.writerow(self.header)    # write the header
            writer.writerows(big_list)      # write the data

if __name__ == "__main__":
    engine = TagFilter(sys.argv[1:])
    engine.execute()