import requests
from datetime import datetime, timedelta
import json
import sys
import argparse
from requests.sessions import default_headers
import urllib3

#to disable warnings for not verifying host
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class labeling:

    def __init__(self, cli_args):
        #initializes arguement parser
        arg_parser = self.__initialize_argument_parser()
        self.args = arg_parser.parse_args(cli_args)
        self.api_url = "https://api2.rhombussystems.com"
        #starts one api session that is used by all requests
        self.api_sess = requests.session()
        self.api_sess.headers = {
            "x-auth-scheme": "api-token",
            "x-auth-apikey": self.args.APIkey}

    @staticmethod
    def __initialize_argument_parser():
        parser = argparse.ArgumentParser(
            description= "Batch labels people based on the names inserted")
        #aruements avaiable for the user to customize
        parser.add_argument('APIkey', type=str, help='Get this from your console')
        parser.add_argument('choice', type=str, help='Do you want to add or remove a string', choices=['remove', 'add'])
        parser.add_argument('label', type=str, help='What is the name of the new label')
        parser.add_argument('names', type=str, help='What are the names you want to add to the label (separate names with commas; name, name, name)')
        return parser

    #adds a label to all of the names
    def add_label(self, event):
        # url of the api
        endpoint = self.api_url + "/api/face/addFaceLabel"
        # any parameters
        payload = {
            "faceIdentifier" : event,
            "label" : self.args.label
        }
        resp = self.api_sess.post(endpoint, json=payload,
        verify=False)
        content = resp.content
        data = json.loads(content)

    def remove_label(self, event):
        # url of the api
        endpoint = self.api_url + "/api/face/removeFaceLabel"
        # any parameters
        payload = {
            "faceIdentifier" : event,
            "label" : self.args.label
        }
        resp = self.api_sess.post(endpoint, json=payload,
        verify=False)
        content = resp.content
        data = json.loads(content)

    #formats the names to then put them in a list instead of one long string
    def names(self):
        self.args.names = self.args.names.replace(", ", ",")
        self.names_list = self.args.names.split(",")

    def execute(self):
        self.names()
        if self.args.choice == 'add':
            for event in self.names_list:
                self.add_label(event)
        elif self.args.choice == 'remove':
            for event in self.names_list:
                self.remove_label(event)

if __name__ == "__main__":
    engine = labeling(sys.argv[1:])
    engine.execute()