###################################################################################
# Copyright (c) 2021 Rhombus Systems                                              #
#                                                                                 # 
# Permission is hereby granted, free of charge, to any person obtaining a copy    #
# of this software and associated documentation files (the "Software"), to deal   #
# in the Software without restriction, including without limitation the rights    #
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell       #
# copies of the Software, and to permit persons to whom the Software is           #
# furnished to do so, subject to the following conditions:                        #
#                                                                                 # 
# The above copyright notice and this permission notice shall be included in all  #
# copies or substantial portions of the Software.                                 #
#                                                                                 # 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR      #
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,        #
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE     #
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER          #
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,   #
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE   #
# SOFTWARE.                                                                       #
###################################################################################

import requests
import time
import json
import sys
import argparse
import urllib3
import subprocess as sp


#to disable warnings for not verifying host
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class EnvironmentalSwitch():

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
        
    @staticmethod
    def __initalize_argument_parser():
        parser = argparse.ArgumentParser(
            description= "Kill Swicth")
        #aruements avaiable for the user to customize
        parser.add_argument('APIkey', type=str, help= 'What is your API key')
        parser.add_argument('EnvironmentSensor', type=str, help= 'What is the name of your environment sensor to check')
        parser.add_argument('-a', '--Alias', type=str, help='What is the alias of the string')
        parser.add_argument('-i', '--Host', type=str, help='What is the host ip of the strip')
        parser.add_argument('Plug', type=int, help='What plug do you want to turn on or off')
        parser.add_argument('--hot', type=int, help='What is the highest temperature mark you want to set in farenheit', default= 75)
        parser.add_argument('--cold', type=int, help='What is the ecold temperature mark you want in farenheit', default= 70)
        return parser
    
    # to turn off the plug
    def kill(self):
        if self.args.Host:
            output = sp.getoutput('kasa --strip --host ' + self.args.Host + ' off --index ' + str(self.args.Plug - 1 ))
        elif self.args.Alias:
            output = sp.getoutput('kasa --strip --alias ' + self.args.Alias + ' off --index ' + str(self.args.Plug - 1))

    # to turn on the plug
    def on (self):
        if self.args.Host:
            output = sp.getoutput('kasa --strip --host ' + self.args.Host + ' on --index ' + str(self.args.Plug - 1 ))
        elif self.args.Alias:
            output = sp.getoutput('kasa --strip --alias ' + self.args.Alias  + ' on --index ' + str(self.args.Plug - 1))

    # convert celsius to farenheit
    def celsius_convert_to_farenheit(self, celsius):
        farenheit = round((celsius * 1.8) + 32)
        return farenheit

    #get the climate data to get current temperature
    def climate_data(self):
        # url of the api
        endpoint = self.api_url + "/api/climate/getMinimalClimateStateList"
        payload = {
        }
        resp = self.api_sess.post(endpoint, json=payload,
        verify=False)
        content = resp.content
        data = json.loads(content)
        for value in data['climateStates']:
            if (self.args.EnvironmentSensor == value['name']):
                celsius = value['temperatureCelcius']
                return celsius
        print("Error: No environment sensor was found with that name")
        quit()

    def execute(self):
        running = True
        while running == True:
            celsius = self.climate_data()
            farenheit = self.celsius_convert_to_farenheit(celsius)
            # checks if temp is too hot
            if farenheit > self.args.hot:
                self.kill()
            #checks if temp is too cold
            elif farenheit < self.args.cold:
                self.on()
            time.sleep(1)

if __name__ == "__main__":
    engine = EnvironmentalSwitch(sys.argv[1:])
    engine.execute()
