import requests
import argparse
import sys
import json
import csv
import time
import os
import numpy
import tkinter
from PIL import Image, ImageTk

topx,topy,botx,boty = 0,0,0,0
selectRect = None
selecting = False

class isDeskOccupied:

    #Set up workspace for API calls to Rhombus Systems
    def __init__(self,args):
        #Initialize argument parser
        self.argParser = self.__initArgParser()
        self.args = self.argParser.parse_args(args)
        if self.args.dgui:
            self.args.gui == False
        #Create a session to set default call Header information
        self.session = requests.session()
        #self.session.headers = {"x-auth-scheme": "api-token","x-auth-apikey": self.args.apiKey}
        self.session.headers = {"x-auth-scheme": "api-token","x-auth-apikey": self.args.apiKey}
        #Set a default base URL for api calls
        self.url = "https://api2.rhombussystems.com/api/"
        self.time = time.time()
        self.areas = []
        self.debugAreas = []

    #Define arguments which the user may be prompted for
    @staticmethod
    def __initArgParser():
        argParser = argparse.ArgumentParser(description = 'Determine wether defined workspaces are occupied or not on a camera by camera basis')
        argParser.add_argument("apiKey", help = 'Your personal api key, get this from your Rhombus Console')
        argParser.add_argument("uuid", help = 'UUID of target Camera')
        argParser.add_argument("--newArea","--n", help = 'Input a string to define a new area bounding box, must include quotation marks eg: "(0,0)(5,10)"')
        argParser.add_argument("--removeArea","--r", help = 'Open a command line menu to remove an area', action = 'store_true')
        argParser.add_argument("--gui",help = 'Opens an image from the target camera and overlays existing areas over it. Draw and delete areas. Overrides concurrent CLA addition and Deletion actions',action = 'store_true')
        argParser.add_argument("--dgui",help = 'Runs check of defined areas then Opens a Debugging GUI which displays motion event bounding boxes alongside user defined areas',action = 'store_true')
        argParser.add_argument("--ratio")
        return argParser
    
    #Load user defined areas from uuid.csv
    def loadAreas(self):
        try:
            with open(self.args.uuid+'.csv') as csvInput:
                inputReader = csv.reader(csvInput)
                for row in inputReader:
                    row = [int(i) for i in row]#parse each row into ints
                    self.areas.append(row)#add each row to areas
        except FileNotFoundError:
            pass

    #Define a new area
    def newArea(self):
        #Parse the area to add from commandline "(x,y)(x,y)"
        str = self.args.newArea.split(')(')
        newCoords = str[0].split('(')[1].split(',')
        newCoords+=(str[1].split(')')[0].split(','))

        with open(self.args.uuid+'.csv', 'a') as csvOutput:#write new area to uuid.csv
            outputWriter = csv.writer(csvOutput)
            outputWriter.writerow(newCoords)

    #Open a commandline interface to remove an area
    def removeArea(self):
        try:
            #Print all area coords as a menu, take input from user
            with open(self.args.uuid+'.csv') as csvInput:
                inputReader = csv.reader(csvInput)
                i = 1
                areas = []
                for row in inputReader:
                    areas.append(row)
                    print(str(i)+": ("+row[0]+","+row[1]+"),("+row[2]+","+row[3]+")")#Print area bounds and associated index
                    i+=1
                inputReader.close()

            if len(areas) == 0:#Return out if there are no areas to remove
                print("There are no areas to remove")
                return

            print("Enter the index of the area to remove:")
            removeMe = int(input())#Take user input and remove index from area list
            areas.pop(removeMe-1)

            with open(self.args.uuid+'.csv', 'w') as csvOutput:#write updated area list to uuid.csv
                outputWriter = csv.writer(csvOutput)
                for row in areas:
                    outputWriter.writerow(row)

        except FileNotFoundError:
            print("There are no areas to remove")
    
    #Check areas for occupancy
    def checkAreas(self):
        #api/event/getPolicyAlertGroupsForDevice -> event UUID
        #Event UUID -> api/event.getPolicyAlertDetials -> Bounding Box Coords

        #For each Area:
            #For each Human Motion Event:
                #if 4 bounds contained: Area Occupied
                #if >2 bounds contained and substantial motion: Area Occupied
                #Else: Area Not Occupied

        ##Get recent motionGrid
        payload = {
            "deviceUuid": self.args.uuid,
            "endTimeUtcSecs": self.time,
            "startTimeUtcSecs": self.time-300
        }
        motionGrid = self.session.post(self.url+"event/getMotionGrid",json=payload)
        if motionGrid.status_code != 200:#Check for unexpected return
            print("Failure to get motionGrid (api/event/getMotionGrid)")
            return
        motionGrid = json.loads(motionGrid.text)
        motionGrid = motionGrid["motionCells"]
        map = numpy.zeros((36,64))
        for event in motionGrid:#Load motion grid into an array for access to use later
            for pair in motionGrid[event]:
                map[pair["row"]][pair["col"]] += 1

        ##Get recent events
        payload = {
            "deviceUuid": self.args.uuid,
            "maxResults": 1
        }        
        currentEvents = self.session.post(self.url+"event/getPolicyAlertGroupsForDevice",json = payload)
        if currentEvents.status_code != 200:
            print("Failure to get currentEvents (event/getPolicyAlertGroupsForDevice)")
            print(currentEvents)
            return
        currentEvents = json.loads(currentEvents.text)
        currentEvents = currentEvents["policyAlertGroups"][0]
        eventEndTime = currentEvents.get("endTime")

        print("Checking occupancy as of %i minutes ago" % int((self.time-(eventEndTime/1000))/60))
        print("[-1: Unoccupied | 0: Maybe Occupied | 1: Occupied]\n")

        currentEvents = currentEvents.get("policyAlerts")[0]
        if "MOTION_HUMAN" in currentEvents["policyAlertTriggers"]:
            eventUuid = currentEvents["uuid"]
        else:
            return
        ##Get Bounding box of each identified Human Motion Event
        humanMovementBounds = []
        payload = {
            "policyAlertUuid": eventUuid
        }
        eventDetails = self.session.post(self.url+"event/getPolicyAlertDetails",json=payload)
        #store event bounds
        eventDetails = json.loads(eventDetails.text)["policyAlert"]["boundingBoxes"]
        for box in eventDetails:
            left = int((box.get("left")/10000) * 1920)
            right = int((box.get("right")/10000) * 1920)
            top = int((box.get("top")/10000) * 1080)
            bottom = int((box.get("bottom")/10000) * 1080)
            humanMovementBounds.append([left,right,top,bottom])
            if self.args.dgui:
                self.debugAreas.append([left,top,right,bottom])
        ##Compare user defined workspaces to Human Movement Bounding Boxes
        i = 1
        for area in self.areas:
            occupied = -1
            print(i,": ",area)
            i+=1
            for bound in humanMovementBounds:
                overlapCount = 0
                #Determine number of corners in area
                top = (area[1] < bound[2] < area[3]) or (area[3] < bound[2] < area[1])
                bottom = (area[1] < bound[3] < area[3]) or (area[3] < bound[3] < area[1])
                if area[0] < bound[0] < area[2] or area[2] < bound[0] < area[0]:
                    overlapCount+=top
                    overlapCount+=bottom
                if area[0] < bound[1] < area[2] or area[2] < bound[1] < area[0]:
                    overlapCount+=top
                    overlapCount+=bottom

                if overlapCount == 4:
                    occupied = 1
                    break
                else: 
                    if overlapCount >= 2:
                        ##check motion in area
                        #Convert Area bounds to heatMap Coords
                        left = int(area[0]/(1920/64))
                        right = int(area[2]/(1920/64))
                        top = int(area[1]/(1080/36))
                        bottom = int(area[3]/(1080/36))
                        
                        #motion = 0
                        #for j in range(abs(bottom-top)):
                        #    for i in range(abs(right-left)):
                        #        motion+=map[j][i]

                        #if motion > 1:#1 is a placeholder, should use a ratio of some kind
                        occupied = 0
                        break
                #area is not occupied by this event
                continue
            print('\t',occupied)

    #Display an image which will allow a user to manage defined areas
    def gui(self):
        global selectRect
        global selecting
        global botx,boty,topx,topy

        def draw():
            global selectRect
            canvas.delete("all")
            canvas.create_image(0, 0, image=img, anchor=tkinter.NW)
            selectRect = canvas.create_rectangle(topx, topy, topx, topy,dash=(2,2), fill='', outline='white')
            for area in self.areas:
                canvas.create_rectangle(area[0], area[1], area[2], area[3], fill='', outline='green',width = 2)
            if self.args.dgui:
                for area in self.debugAreas:
                    canvas.create_rectangle(area[0], area[1], area[2], area[3], fill='', dash = (2,2),outline='yellow',width = 2)


        def addArea(event):
            global selecting
            global selectRect
            global topx,topy, botx, boty
            if not selecting:
                topx = event.x
                topy = event.y
                selecting = True
                return
            else:
                newCoords = [topx,topy,botx,boty]
                with open(self.args.uuid+'.csv', 'a') as csvOutput:
                    outputWriter = csv.writer(csvOutput)
                    outputWriter.writerow(newCoords)
                    self.areas.append(newCoords)
                topy,topx,boty,botx = 0,0,0,0
                canvas.coords(selectRect, topx, topy, botx, boty)
                selecting = False
                draw()

        def updateSelectRect(event):
            window.title("Double Click to define new areas - Click to Remove :"+str(event.x)+","+str(event.y))
            global selecting
            if not selecting:
                return
            global selectRect
            global topy, topx, botx, boty
            botx, boty = event.x, event.y
            canvas.coords(selectRect, topx, topy, botx, boty)

        def removeArea(event):
            i = len(self.areas)-1
            for area in self.areas[::-1]:
                if (area[0] < event.x < area[2]) or (area[2] < event.x < area[0]):
                    if (area[1] < event.y < area[3]) or (area[3] < event.y < area[1]):
                        self.areas.pop(i)
                        break
                i-=1
            with open(self.args.uuid+'.csv', 'w') as csvOutput:
                outputWriter = csv.writer(csvOutput)
                for row in self.areas:
                    outputWriter.writerow(row)
            draw()

        payload = {
        "cameraUuid": self.args.uuid,
        "timestampMs": (self.time)*1000
        }
        frameURI = self.session.post(self.url+"video/getExactFrameUri", json = payload)
        frameURI = json.loads(frameURI.text)["frameUri"]
        with open("tempFrame.jpg", "wb") as output_fp:
            frame_resp = self.session.get(frameURI)
            output_fp.write(frame_resp.content)
            output_fp.flush()
            frame_resp.close()

        window = tkinter.Tk()
        window.title("Double Click to define new areas - Click to Remove")
        window.geometry('1920x1080')
        window.configure(background='grey')

        img = ImageTk.PhotoImage(Image.open('tempFrame.jpg'))
        canvas = tkinter.Canvas(window, width=img.width(), height=img.height(),borderwidth=0, highlightthickness=0)
        canvas.pack(expand=True)
        os.remove('tempFrame.jpg')

        draw()
        canvas.bind('<Double-Button-1>', addArea)
        canvas.bind('<Button-1>', removeArea)
        canvas.bind('<Motion>', updateSelectRect)

        window.mainloop()

    def execute(self):
        self.loadAreas()
        if(self.args.gui):
            self.gui()
        else:
            if(self.args.newArea):
                self.newArea()
            if(self.args.removeArea):
                self.removeArea()

        self.checkAreas()

        if self.args.dgui:
            self.gui()
        return

if __name__ == "__main__":
    engine = isDeskOccupied(sys.argv[1:])
    engine.execute()