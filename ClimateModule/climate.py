from datetime import datetime, timedelta
import requests
import argparse
import calendar
import urllib3
import time
import json
import sys

# to disable warnings for not verifying host
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Climate:
    def __init__(self, cli_args):
        arg_parser = self.__initialize_argument_parser()
        self.args = arg_parser.parse_args(cli_args)
        self.api_url = "https://api2.rhombussystems.com"
        self.api_sess = requests.session()
        self.api_sess.headers = {
            "Accept": "application/json",
            "x-auth-scheme": "api-token",
            "Content-Type": "application/json",
            "x-auth-apikey": self.args.APIkey
        }

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
            description = "Gets the rate of change of the temperature."
        )
        
        # optional arguments for the user
        parser.add_argument("APIkey", type=str, help="Get this from your console")
        parser.add_argument("sensorName", type=str, help="Name of the Environmental Sensor")
        parser.add_argument("--time", type=str, help="Time")
        
        return parser

    # converts human time to milliseconds  
    def milliseconds_time(self, human):
        # the +25200000 is to get it to local time and not GMT
        ms_time = (calendar.timegm(time.strptime(human, '%Y-%m-%d %H:%M:%S')) * 1000) + 25200000
        return ms_time 

    # converts the ms time to timestamp
    def human_time(self, event):
        event = event/1000
        timestamp = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(event))
        return timestamp

    # converts milliseconds to minutes
    def ms_convert(self, milliseconds):
        seconds = milliseconds / 1000
        minutes = seconds / 60
        return minutes

    # converts sensor name to sensor uuid
    def sensor_name_convert(self):
        for value in self.sensor_name_data['climateStates']:
            if self.args.sensorName == value['name']:
                return value['sensorUuid']

    # converts celsius to Fahrenheit
    def celsius_convert(self, celsius):
        fahrenheit = (celsius * 1.8) + 32
        return fahrenheit
 
    # returns data that is used to convert the sensor name to uuid
    def sensor_data(self):
        endpoint = self.api_url + "/api/climate/getMinimalClimateStateList"
        payload = {
        }
        resp = self.api_sess.post(endpoint, json = payload,
        verify = False)
        content = resp.content
        sensor_name_data = json.loads(content)

        return sensor_name_data
 
    # returns temperature and humidity data 
    def climate_data(self):
        endpoint = self.api_url + "/api/climate/getClimateEventsForSensor"
        self.sensor_name_data = self.sensor_data()
        sensor_uuid = self.sensor_name_convert()
        ms_time = self.milliseconds_time(self.args.time)  # Time that values will be calculated for
        ms_time_begin = ms_time - (90000 * 8)  # start time for data collection is 2 hours before the time specified by the user 
        ms_time_end = ms_time + (90000 * 8)    # end time for data collection is 2 hours after the time specified by the user 
        payload = {
            "sensorUuid": sensor_uuid,
            "createdAfterMs": ms_time_begin,
            "createdBeforeMs": ms_time_end
        }
        resp = self.api_sess.post(endpoint, json=payload,
        verify=False)
        content = resp.content
        data = json.loads(content)
    
        return data

    def execute(self):
        climate_data = self.climate_data()
        count = 0
        
        if 'climateEvents' not in climate_data:  
            print("There is no data for that tag name.")
            return

        for earlier_time in climate_data['climateEvents']:
            count += 1
            ms_time = self.milliseconds_time(self.args.time)

            if earlier_time['timestampMs'] < ms_time:
                later_time = climate_data['climateEvents'][count - 2]
                time_dif_ms = later_time['timestampMs'] - earlier_time['timestampMs']  
                time_dif_min = self.ms_convert(time_dif_ms)   # convert the time difference in ms to minutes 
                temp_dif = self.celsius_convert(later_time['temp']) - self.celsius_convert(earlier_time['temp'])   # calculate the temperature difference in Fahrenheit
                humid_dif = later_time['humidity'] - earlier_time['humidity']
                temp_rate_min = temp_dif / time_dif_min    # change in temperature per minute
                humid_rate_min = humid_dif / time_dif_min  # change in humidity per minute

                print("The temperature is changing at a rate of %.4f ℉ per minute" % temp_rate_min)
                print("The humidity is changing at a rate of %.4f percent per minute" % humid_rate_min)
                break
        
        if count == 0:   
            print("There is no data for that date.")

if __name__ == "__main__":
    engine = Climate(sys.argv[1:])
    engine.execute()