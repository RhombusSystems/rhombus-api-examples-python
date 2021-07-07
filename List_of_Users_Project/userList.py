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

class List:
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
            description= "Gets a report of all of the Users and their emails.")
        #aruements avaiable for the user to customize
        parser.add_argument('APIkey', type=str, help='Get this from your console')
        parser.add_argument('-c', '--csv', type=str, help= 'Name the csv file', default='csvFile.csv')
        parser.add_argument('-p', '--path', type=str, help='Path to where the csv will go', default=os.getcwd())
        return parser

    def getUsers(self):
        # url of the api
        endpoint = self.api_url + "/api/user/getUsersInOrg"
        # any parameters
        payload = {
        }
        resp = self.api_sess.post(endpoint, json=payload,
        verify=False)
        content = resp.content
        data = json.loads(content)
        return data

    def csv_add(self, value, data_Users):
        self.csv_data.append([])
        self.name = value['name']
        self.csv_data[self.count].append(self.name)
        self.csv_data[self.count].append(value['emailCaseSensitive'])
        with open(self.args.path + '/' + self.args.csv, 'w', newline = '') as f:
            writer = csv.writer(f)     # create the csv writer
            writer.writerow(self.header)    # write the header
            writer.writerows(self.csv_data) # write the data

    def execute(self):
        self.count = 0
        data_Users = self.getUsers()
        self.header = ['Name', 'Email']
        self.csv_data = []
        for value in data_Users['users']:
            self.csv_add(value, data_Users)
            self.count += 1

if __name__ == '__main__':
    engine = List(sys.argv[1:])
    engine.execute()