import requests
import argparse
from datetime import datetime
import sys
import csv
import matplotlib.pyplot as plt

class UpTime:
    #Set up workspace for API calls to Rhombus Systems
    def __init__(self,args):
        #Initialize argument parser
        self.argParser = self.__initArgParser()
        self.args = self.argParser.parse_args(args)
        if self.args.timespan:
            self.args.timespan = int(self.args.timespan)
        else:
            self.args.timespan = 24
        #Create a session to set default call Header information
        self.session = requests.session()
        self.session.headers = {"x-auth-scheme": "api-token","x-auth-apikey": self.args.apiKey}
        #Set a default base URL for api calls
        self.url = "https://api2.rhombussystems.com/api/"
        self.curTime = int(datetime.utcnow().timestamp())

    #Define arguments which the user may be prompted for
    @staticmethod
    def __initArgParser():
        argParser = argparse.ArgumentParser(description='Creates and displays a visual representation of sensor uptime within an organizatiopn over a given timespan')
        argParser.add_argument("apiKey", help = 'This is your individual Rhombus Console API Key')
        argParser.add_argument("--timespan", help = 'Hours prior to the current time to include in visual (Default value is 24)')
        return argParser

    def uptimeVisualizer(self):
        response = self.session.post(self.url+"export/diagnostic")#Get Diagnostic logs
        if response.status_code != 200:#Check for unexpected results
            print("Encountered an Error getting diagnostic logs")
            return
        decoded_content = response.content.decode('utf-8')
        diagnosticReport = csv.reader(decoded_content.splitlines(), delimiter=',')
        diagnosticReport = list(diagnosticReport)

        devices = []#Stores list of devices
        disconnectTime = []#Temporary storage for disconnect times
        upTimeTuples = []#Stores a list of tuples representing uptime for each sensor, format ->(startTime,duration)
        uptime = []#Stores total uptime within defined timespan per sensor

        #Logs are read in order from most recent to oldest
        #If Device is connecting, combine connection time with disconnection time to define uptime window
        #If Device is disconnecting, store disconnection time for use with its connection time later

        #Populate Device list and find Device Uptime Windows
        for log in diagnosticReport[1:]:
            if log[2] in devices:#if the current device is accounted for
                index = devices.index(log[2])
                if "CAMERA_DISCONNECTED" in log[3] or "OFFLINE" in log[3]:#If the device is disconnecting
                    disconnectTime[index] = datetime.strptime((log[0]+" "+log[1]), "%Y-%m-%d %H:%M:%S+00:00").timestamp()/60/60
                elif ("CAMERA_CONNECTED" in log[3] or "ONLINE" in log[3]) and disconnectTime[index] != None:#If the device is connecting
                    eventTime = datetime.strptime((log[0]+" "+log[1]), "%Y-%m-%d %H:%M:%S+00:00").timestamp()/60/60
                    eventDuration = disconnectTime[index]-eventTime
                    disconnectTime[index] = None
                    upTimeTuple = tuple((eventTime,eventDuration))
                    upTimeTuples[index].append(upTimeTuple)
            else:#if the current device is not accounted for
                if "CAMERA_DISCONNECTED" in log[3] or "OFFLINE" in log[3]:#If the device is disconnecting
                    devices.append(log[2])#Add Device to list
                    upTimeTuples.append([])#Create list for devices uptime windows
                    uptime.append(0)#Create space to store total uptime
                    disconnectTime.append(datetime.strptime((log[0]+" "+log[1]), "%Y-%m-%d %H:%M:%S+00:00").timestamp()/60/60)
                elif "CAMERA_CONNECTED" in log[3] or "ONLINE" in log[3]:#If the device is connecting
                    devices.append(log[2])#Add Device to list
                    index = devices.index(log[2])#Get Index of device
                    upTimeTuples.append([])#Create list for devices uptime windows
                    uptime.append(0)#Create space to store total uptime
                    eventTime = datetime.strptime((log[0]+" "+log[1]), "%Y-%m-%d %H:%M:%S+00:00").timestamp()/60/60
                    eventDuration = (self.curTime/60/60)-eventTime
                    upTimeTuple = tuple((eventTime,eventDuration))
                    disconnectTime.append(0)#Expand disconnect times
                    upTimeTuples[index].append(upTimeTuple)

        #Iterate through each devices uptime tuples to calculate total uptime within the selected timespan
        i = 0
        for device in upTimeTuples:#For each device
            for ts in device:#For each window
                if ts[0] > ((self.curTime/60/60) - self.args.timespan):#If window is entirely within timespan
                    uptime[i]+=ts[1]#add eventduration to total uptime
                    continue
                if (ts[0] + ts[1]) > ((self.curTime/60/60) - self.args.timespan):#If uptime window is partly within the bounds
                    uptime[i]+=ts[0]+ts[1]-((self.curTime/60/60) - self.args.timespan)#Calculate overlap and add to total uptime
                    break
            i+=1

        #Convert uptime into percentage
        i=0
        for value in uptime:
            value = value/self.args.timespan*100
            uptime[i] = int(value)
            i+=1

        #Combine upTime,Devices,and upTimeTuples together so they can be sorted together
        data = list(zip(uptime,devices,upTimeTuples))
        data.sort()
        
        #Create Chart
        fig, ax = plt.subplots(figsize = (20,5))
        axR = ax.twinx()

        ax.set_title("Sensor Uptime")

        ax.set_ylabel('Devices')
        ax.set_ylim(0,len(data)+1)
        ax.set_yticks(range(1,len(data)+1))
        ax.set_yticklabels([x[1] for x in data])#Parse devices from data zip

        axR.set_ylabel('Uptime Percentage')
        axR.set_ylim(0,len(data)+1)
        axR.set_yticks(range(1,len(data)+1))
        axR.set_yticklabels([x[0] for x in data])#Parse uptime from data zip

        ax.set_xlabel('Hours since epoch')
        ax.set_xlim(int(self.curTime/60/60)-self.args.timespan, int(self.curTime/60/60))

        ax.grid(False)

        index = 0
        colors = ['#3e8ce9','#4cadde']
        for listTuples in [x[2] for x in data]:#Parse uptime window lists from data zip
            ax.broken_barh(listTuples, (index+.625,.75), facecolors=colors[index%len(colors)],edgecolor = "black")#Add each set to graph
            index+=1

        plt.show()#Display graph

if __name__ == "__main__":
    engine = UpTime(sys.argv[1:])
    engine.uptimeVisualizer()
