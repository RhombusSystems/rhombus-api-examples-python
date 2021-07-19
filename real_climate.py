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

class Climate:
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
            description = "Gets the rate of change of the temperature."
        )
        # command line arguments for user
        parser.add_argument("APIkey", type=str, help="Get this from your console")
        parser.add_argument("sensorName", type=str, help="Name of the Environmental Sensor")
        parser.add_argument("option", type = str, help = "Whether the program should look for past or present events", choices = ["Past", "Present"])
        parser.add_argument("--time", type=str, help="yyyy-mm-dd (0):00:00")
        parser.add_argument("--tempRate", type = float, help = "The limit for which the ratechange of the temperature is OK.", default = 0.015)
        parser.add_argument("--humidRate", type = float, help = "The limit for which the ratechange of the humidity is OK.", default = 0.015)
        parser.add_argument("--cameraName", type = str, help = 'Name of the camera that is associated with the environmental sensor.')

        return parser

    # converts human time to milliseconds  
    def milliseconds_time(self, human):
        # the +25200000 is to get local time and not GMT
        ms_time = (calendar.timegm(time.strptime(human, '%Y-%m-%d %H:%M:%S')) * 1000) + 25200000
        return ms_time 

    # converts ms time to timestamp
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
        for value in self.sensor_data['climateStates']:
            if self.args.sensorName == value['name']:
                return value['sensorUuid']

    # converts camera name to camera uuid
    def camera_name_convert(self):
        for value in self.camera_data['cameraStates']:
            if self.args.cameraName == value['name']:
                return value['uuid']

    # converts Celsius to Fahrenheit
    def celsius_convert(self, celsius):
        fahrenheit = (celsius * 1.8) + 32
        return fahrenheit

    # returns data that is used to convert sensor namse to uuid
    def sensor(self):
        endpoint = self.api_url + "/api/climate/getMinimalClimateStateList"
        payload = {
        }
        resp = self.api_sess.post(endpoint, json = payload,
        verify = False)
        content = resp.content
        sensor_data = json.loads(content)

        return sensor_data

    # returns data that is used to convert camera name to uuid
    def camera_data(self):
        endpoint = self.api_url + "/api/camera/getMinimalCameraStateList"
        payload = {
        }
        resp = self.api_sess.post(endpoint, json = payload, 
        verify = False)
        content = resp.content
        data = json.loads(content)

        return data

    # returns temperature and humidity data 
    def climate_data(self, start_time, end_time):
        endpoint = self.api_url + "/api/climate/getClimateEventsForSensor"
        self.sensor_data = self.sensor()
        self.sensor_uuid = self.sensor_name_convert()
    
        payload = {                   
            "sensorUuid": self.sensor_uuid,
            "createdAfterMs": start_time,
            "createdBeforeMs": end_time
        }
        resp = self.api_sess.post(endpoint, json=payload,
        verify=False)
        content = resp.content
        data = json.loads(content)

        return data

    # creates seekpoint 
    def create_seekpoint(self):
        self.camera_data = self.camera_data()

        if self.args.cameraName:
            self.cameraUuid = self.camera_name_convert()
        else:
            for value in self.sensor_data['climateStates']:
                if len(value["associatedCameras"]) > 0:
                    self.cameraUuid = value['associatedCameras'][0]
                    # 'associatedCameras' is a list
                    # program will use the first value in the list 
                else:
                    # if there are no camera uuids in the list 
                    print("There are no cameras associated with this sensor.")
                    return

        endpoint = self.api_url + "/api/camera/createFootageSeekpoints"
        payload = {
            "footageSeekPoint": {
                "a": "CUSTOM", 
                "cdn": "Rapid Temp/Humidity Change",
                "ts": self.ms_time
            },
            "cameraUuid": self.cameraUuid
        }
        resp = self.api_sess.post(endpoint, json=payload,
        verify=False)
        content = resp.content
        data = json.loads(content)
        return data

    def execute(self):
        temp_rate_min = None   # declaring temp_rate_min to validate the date
        count = 0

        if self.args.option == "Past":
            if self.args.time:
                self.ms_time = self.milliseconds_time(self.args.time)  # if input, converting timestamp to milliseconds
            else:
                self.ms_time = int(round((time.time() - 60 * 60 * 2) * 1000)) # defaults to two hours ago
            
            ms_time_begin = self.ms_time - (15 * 60 * 1000)  # start time of data collection is 15 minutes before ms_time
            ms_time_end = self.ms_time + (15 * 60 * 1000)    # end time of data collection is 15 minutes after ms_time 
    
            climate_data = self.climate_data(ms_time_begin, ms_time_end)

            if 'climateEvents' not in climate_data:  # input validation for sensor name 
                print("There is no data for that tag name.")
                return 

            # running through times in ms (greatest to least)
            for earlier_time in climate_data['climateEvents']:
                count += 1
                # in milliseconds, an earlier time would be a lesser number than a later time
                if earlier_time['timestampMs'] < self.ms_time:  
                    later_time = climate_data['climateEvents'][count - 2] 
                    # later_time is the closest time that is later than ms_time
                    time_dif_ms = later_time['timestampMs'] - earlier_time['timestampMs']  # time difference in milliseconds 
                    time_dif_min = self.ms_convert(time_dif_ms)   # ms time difference is converted to minutes 
                    temp_dif = self.celsius_convert(later_time['temp']) - self.celsius_convert(earlier_time['temp'])   
                    # temperature difference between the two times is calculated in Fahrenheit
                    humid_dif = later_time['humidity'] - earlier_time['humidity']
                    # humidity difference between the two times is calculated in Fahrenheit
                    temp_rate_min = temp_dif / time_dif_min    # change in temperature per minute
                    humid_rate_min = humid_dif / time_dif_min  # change in humidity per minute
            
            print("Temperature rate of change: ", temp_rate_min)
            print("Humidity rate of change: ", humid_rate_min)
        
            if temp_rate_min == None:  # no data generated if temp_rate_min is still None, date must be invalid
                print("There are no data for the data.")
                return

            # if rate at which the temperature is changing exceeds threshold 
            if temp_rate_min > self.args.tempRate or temp_rate_min < -self.args.tempRate:
                self.create_seekpoint()
                if self.cameraUuid == None:  # self.cameraUuid will be none if cameraName is invalid
                    print("Invalid camera name, no seekpoint created.")
                else:  
                    print("Temperature exceeded threshold, seekpoint created.")

            # if rate at which the humidity is changing exceeds threshold 
            elif humid_rate_min > self.args.humidRate or humid_rate_min < -self.args.humidRate:
                self.create_seekpoint()
                if self.cameraUuid == None:  # self.cameraUuid will be none if cameraName is invalid
                    print("Invalid camera name, no seekpoint created.")
                else:
                    print("Humidity exceeded threshold, seekpoint created.")
            else:
                print("No seekpoints created.")

        else: # if the user chose the option of past 
            running = True

            temp_list = [] # list of temperature in Fahrenheit
            humid_list = [] # list of humidities
            time_list = [] # list of times in milliseconds 

            while running == True:
                print("Processing ... ")
                end_time = int(round(time.time() * 1000))  # end time of data collection is always the current time
                start_time = end_time - (1000 * 210)   # start time of data collection is always 210 seconds before current time

                climate_data = self.climate_data(start_time, end_time)

                # print("end time: ", end_time)
                # print("start time: ", start_time)

                for value in climate_data['climateEvents']:
                    if self.celsius_convert(value['temp']) not in temp_list:
                        temp_list.append(self.celsius_convert(value['temp'])) # append fahrenheit to temp_list 
                        humid_list.append(value['humidity']) # append humidity to humid_list
                        time_list.append(value['timestampMs']) # append milliseconds to time_list

                count = 0

                if len(temp_list) > 1: # if there are multiple events 
                    # running through the events
                    while count < len(temp_list) - 1:
                        # calc the time difference between events in milliseconds 
                        time_dif_ms = time_list[count + 1] - time_list[count] 
                        time_dif_min = time_dif_ms / 1000 / 60 # convert time difference to seconds 

                        # calc difference in temperature (Fahrenheits)
                        temp_dif = self.celsius_convert(temp_list[count + 1]) - self.celsius_convert(temp_list[count])
                        humid_dif = humid_list[count] - humid_list[count + 1] # calc difference in humidity 

                        temp_rate_min = temp_dif / time_dif_min  # rate at which the temperature is changing
                        print("Temp rate: ", temp_rate_min)

                        humid_rate_min = humid_dif / time_dif_min # rate at which the humidity is changing 
                        print("Humid rate: ", humid_rate_min)

                        # if rate at which the temperature is changing exceeds threshold 
                        if temp_rate_min > self.args.tempRate or temp_rate_min < -self.args.tempRate:
                            self.ms_time = end_time
                            self.create_seekpoint()
                            print("Temperature rate of change exceeds threshold, seekpoint created.")
                            return 
                        else:
                            print("Temperature rate of change: ", temp_rate_min) 
                            print("Temperate rate of chane does not exceed threshold, no seekpoint created.")

                        # if rate at which the humidity is changing exceeds threshold 
                        if humid_rate_min > self.args.humidRate or humid_rate_min < -self.args.humidRate:
                            self.ms_time = end_time
                            self.create_seekpoint()
                            print("Humidity rate of change exceeds threshold, seekpoint created.")
                            return
                        else:
                            print("Humidity rate of change: ", humid_rate_min) # TODO: create placeholder
                            print("Humidity rate of change does not exceed threshold, no seekpoint created.")

                        count += 1

                time.sleep(60) # sleep for one minute before each data collection

if __name__ == "__main__":
    engine = Climate(sys.argv[1:])
    engine.execute()  
