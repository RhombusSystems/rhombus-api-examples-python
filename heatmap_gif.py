import requests
import argparse
import sys
import os
import json

import seaborn
import numpy
import matplotlib.pyplot
import imageio
class HeatmapGif:
#Set up workspace for API calls to Rhombus Systems
    def __init__(self,args):
        #Initialize argument parser
        self.argParser = self.__initArgParser()
        self.args = self.argParser.parse_args(args)
        #Create a session to set default call Header information
        self.session = requests.session()
        self.session.headers = {"x-auth-scheme": "api-token","x-auth-apikey": self.args.apiKey}
        #Set a default base URL for api calls
        self.url = "https://api2.rhombussystems.com/api/"

    @staticmethod
    def __initArgParser():
        argParser = argparse.ArgumentParser(description="Produces a heatmap GIF summarizing activity across the seelcted timespan")
        argParser.add_argument("apiKey", help="API Access Key, get this form your console.")
        argParser.add_argument("uuid", help = "UUID identifies the target camera")
        argParser.add_argument("startTime", help = "Time in seconds since epoch to start sampling")
        argParser.add_argument("endTime", help = "Time in seconds since epoch to stop sampling")
        argParser.add_argument("stepSize", help = "Time in seconds represented by each frame")
        return argParser

    def execute(self):
        stepSize = int(self.args.stepSize)
        prevTime = int(self.args.startTime)
        endTime = int(self.args.endTime)
        curTime = stepSize+prevTime
        
        steps = (endTime-curTime)/stepSize
        i = 0
        ##Setup writer to output heatmap.gif
        with imageio.get_writer('./heatmap.gif',mode='I') as writer:
            while(curTime <= endTime):
                ##Get data for timeslot
                #Pull Data from /api/event/getMotionGrid - returns a list of times and the grid spaces which contained motion at that time
                payload = {
                    "deviceUuid": self.args.uuid,
                    "endTimeUtcSecs": curTime,
                    "startTimeUtcSecs": prevTime 
                }
                motionGridResponse = self.session.post(self.url+"event/getMotionGrid",json=payload)
                #Check response status code for unexpected result
                if(motionGridResponse.status_code != 200):
                    print("Error requesting Motion Grid (/api/event/getMotionGrid)")
                    print(motionGridResponse.text,"\n")
                    return
                #Prepare motionGrid for parsing
                motionGrid = json.loads(motionGridResponse.text)
                motionGrid = motionGrid["motionCells"]
                ##Create Heatmap
                #Populate an array with count of times motion was detected througout the timeslot
                map = numpy.zeros((36,64))
                for event in motionGrid:
                    for pair in motionGrid[event]:
                        map[pair["row"]][pair["col"]] += 1
                #Generate heatmap plot of data collected and adjust formatting
                matplotlib.pyplot.clf()
                seaborn.heatmap(map,center = stepSize/2, vmin = 0, vmax=stepSize, cbar = False, square=True, cmap="coolwarm")
                ax = matplotlib.pyplot.gca()
                ax.axes.xaxis.set_visible(False)
                ax.axes.yaxis.set_visible(False)
                try:
                    #Save heatMap to png and append to gif
                    matplotlib.pyplot.savefig('heatMap.png')
                    image = imageio.imread('heatMap.png')
                    writer.append_data(image)
                except FileNotFoundError:
                    print("heatMap.png failed to save.")
                    return
                #Increment the time slot
                prevTime = curTime
                curTime += stepSize
                print(str(int((i/steps)*100))+"%")
                i+=1
        print("Done!")
        #Cleanup
        os.remove("heatMap.png")
        return
if __name__ == "__main__":
    engine = HeatmapGif(sys.argv[1:])
    engine.execute()
