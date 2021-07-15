import requests
import argparse
import sys
import json
import csv
import time
import os
import tkinter
from PIL import Image, ImageTk

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
        self.endTime = None
        self.areas = []
        self.humanMovementBounds = []

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

    #Define and save a new area from CLA
    def newArea(self):
        #Parse the area to add from commandline "(x,y)(x,y)"
        str = self.args.newArea.split(')(')
        newCoords = str[0].split('(')[1].split(',')
        newCoords+=(str[1].split(')')[0].split(','))

        with open(self.args.uuid+'.csv', 'a') as csvOutput:#write new area to uuid.csv, opening in 'a' mode creates a new file if one doesn't exist already
            outputWriter = csv.writer(csvOutput)
            outputWriter.writerow(newCoords)

    #Open a commandline interface to remove an area, and save updated area list to uuid.csv
    def removeArea(self):
        try:
            #Print all area coords as a menu, take input from user
            with open(self.args.uuid+'.csv') as csvInput:
                inputReader = csv.reader(csvInput)
                i = 1
                areas = []
                for row in inputReader:
                    areas.append(row)#add row to local list
                    print(str(i)+": ("+row[0]+","+row[1]+"),("+row[2]+","+row[3]+")")#Print area bounds and associated index
                    i+=1

            if len(areas) == 0:#Return if there are no areas to remove
                print("There are no areas to remove")
                return

            print("Enter the index of the area to remove:")
            removeMe = int(input())#Take user input
            areas.pop(removeMe-1)#Remove specified index from list

            with open(self.args.uuid+'.csv', 'w') as csvOutput:#write updated area list to uuid.csv
                outputWriter = csv.writer(csvOutput)
                for row in areas:
                    outputWriter.writerow(row)

        except FileNotFoundError:
            print("There are no areas to remove")
    
    #Check areas for occupancy
    def checkAreas(self):
        ##Summary
        #api/event/getPolicyAlertGroupsForDevice -> event UUID
        #Event UUID -> api/event.getPolicyAlertDetials -> Bounding Box Coords
        #Bounding Box Coords vs. user defined areas -> occupancy
        #For each Area:
            #For each Human Motion Event:
                #if 4 bounds contained: Area Occupied
                #if >=2 bounds contained: Area May Be Occupied
                #Else: Area Not Occupied

        ##Get recent event groups
        payload = {
            "deviceUuid": self.args.uuid,
            "maxResults": 10 #Get 10 most recent policy alerts grouped by time
        }        
        currentEvents = self.session.post(self.url+"event/getPolicyAlertGroupsForDevice",json = payload)
        if currentEvents.status_code != 200:#Check for unexpected status code
            print("Failure to get currentEvents (event/getPolicyAlertGroupsForDevice)")
            return
        currentEvents = json.loads(currentEvents.text)
        currentEvents = currentEvents["policyAlertGroups"][0]#Get the most recent event group
        self.endTime = currentEvents.get("endTime")/1000#Get end time of most recent event group in seconds
        currentEvents = currentEvents.get("policyAlerts")
        eventUuid = []

        for policyAlert in currentEvents:#For each policy alert in the event Group
            #If human motion triggered an event in the event group, get its UUID
            if "MOTION_HUMAN" in policyAlert["policyAlertTriggers"]:
                eventUuid.append(policyAlert["uuid"])

        ##Use the event UUIDs to get event groups details, specifically the bounding boxes associated with the event group
        for uuid in eventUuid:
            payload = {
                "policyAlertUuid": uuid
            }
            eventDetails = self.session.post(self.url+"event/getPolicyAlertDetails",json=payload)
            if eventDetails.status_code != 200:#Check for unexpected status code
                print("Failure to get eventDetails (event/getPolicyAlertDetails)")
                return
            eventDetails = json.loads(eventDetails.text)["policyAlert"]["boundingBoxes"]

            #convert event bounds to pixel coordinates and store
            for box in eventDetails:
                #Convert Permyiads to coordinates -> (value/10000) * total dimension
                left = int((box.get("left")/10000) * 1920)
                right = int((box.get("right")/10000) * 1920)
                top = int((box.get("top")/10000) * 1080)
                bottom = int((box.get("bottom")/10000) * 1080)
                activity = box.get("activity")
                self.humanMovementBounds.append([left,top,right,bottom,activity])
        ##Compare user defined workspaces to Human Movement Bounding Boxes
        print("\nChecking occupancy as of %i minutes ago" % int((self.time-self.endTime)/60))
        print("[-1: Area unoccupied | 0: Area may be occupied | 1: Area occupied]\n")
        i = 1
        for area in self.areas:
            print("%i: (%i,%i)(%i,%i)" % (i,area[0],area[1],area[2],area[3])) #i: (x,y)(x,y)
            i+=1
            occupied = -1 #Occupied value starts as empty, may change from empty but will not return to empty
            for bound in self.humanMovementBounds:
                overlapCount = 0
                #Determine number of corners in area
                top = (area[1] < bound[1] < area[3]) or (area[3] < bound[1] < area[1])#is the top bound within the user defined area?
                bottom = (area[1] < bound[3] < area[3]) or (area[3] < bound[3] < area[1])#is the bottom bound within the user defined area?
                if area[0] < bound[0] < area[2] or area[2] < bound[0] < area[0]:#is the left bound within the user defined area?
                    overlapCount+=top#Top Left Corner
                    overlapCount+=bottom#Bottom Left Corner
                if area[0] < bound[2] < area[2] or area[2] < bound[2] < area[0]:#is the right bound within the user defined area?
                    overlapCount+=top#Top Right Corner
                    overlapCount+=bottom#Bottom Right Corner

                if overlapCount == 4: #if a relevant event is entirely within the bounds of the work area
                    occupied = 1 #Space is occupied, break from loop
                    break
                if overlapCount >= 2: #if a relevant event is partially within the bounds of the work area
                    occupied = 0 #Space may be occupied, continue through loop
                continue
            print('\t',occupied) #print status of the area

    #Display an image which will allow a user to manage defined areas
    def gui(self):
        global selectRect #the dashed rectangle which outlines a selection in progress
        global selecting #a control boolean which tracks the state of user interaction - starts as False
        global botx,boty,topx,topy #coordinates for selectRect
        topx,topy,botx,boty = 0,0,0,0
        selectRect = None
        selecting = False
        ###Gui methods
        def draw():
            global selectRect
            canvas.delete("all")#Clear the Canvas
            canvas.create_image(0, 0, image=img, anchor=tkinter.NW)#Draw Image on Canvas
            selectRect = canvas.create_rectangle(topx, topy, topx, topy,dash=(2,2), fill='', outline='white')#Draw selectRect
            for area in self.areas:
                canvas.create_rectangle(area[0], area[1], area[2], area[3], fill='', outline='green',width = 2)#Draw user defined areas
            if self.args.dgui:
                for area in self.humanMovementBounds:
                    if area[4] == "MOTION_HUMAN":
                        canvas.create_rectangle(area[0], area[1], area[2], area[3], fill='', dash = (2,2),outline='yellow',width = 2)#If in debug mode, draw motion bounds
                    else:
                        canvas.create_rectangle(area[0], area[1], area[2], area[3], fill='', dash = (2,2),outline='purple',width = 2)#If in debug mode, draw motion bounds

        #two part process for adding a new area to track, triggered by double clicking mouse 1
        def addArea(event):
            global selecting 
            global selectRect
            global topx,topy, botx, boty
            if not selecting:#If first trigger, start selecting an area
                topx,topy = event.x,event.y #Set first corner of selection to mouse position
                selecting = True
                return
            else:#On second trigger, finish selecting an area and save selected area
                newCoords = [topx,topy,botx,boty]
                self.areas.append(newCoords)#Append new area to self.areas 
                with open(self.args.uuid+'.csv', 'a') as csvOutput:#Write
                    outputWriter = csv.writer(csvOutput)
                    outputWriter.writerow(newCoords)
                #Reset selectRect
                topy,topx,boty,botx = 0,0,0,0
                canvas.coords(selectRect, topx, topy, botx, boty)
                #end selecting
                selecting = False
                #Redraw frame
                draw()
        #Frame updates associated with motion
        def updateSelectRect(event):
            #Always update title with current mouse position
            window.title("Double Click to define new areas - Click to Remove :"+str(event.x)+","+str(event.y))
            global selecting
            if not selecting:#If not currently selecting an area, return
                return
            #Update selectRect and its coordinates
            global selectRect
            global topy, topx, botx, boty
            botx, boty = event.x, event.y #set second corner of selectRect to mouse position
            canvas.coords(selectRect, topx, topy, botx, boty)

        #Remove the most recently added area which contains the mouse cursor
        def removeArea(event):
            i = len(self.areas)-1
            for area in self.areas[::-1]:#Iterate through self.areas in reverse
                if (area[0] < event.x < area[2]) or (area[2] < event.x < area[0]):#If mouse x pos is in area
                    if (area[1] < event.y < area[3]) or (area[3] < event.y < area[1]):#If mouse y pos is in area
                        self.areas.pop(i)#Remove current index from list, break from loop
                        break
                i-=1
            #write updated list to uuid.csv
            with open(self.args.uuid+'.csv', 'w') as csvOutput:
                outputWriter = csv.writer(csvOutput)
                for row in self.areas:
                    outputWriter.writerow(row)
            draw()#redraw frame
        ###Gui Main
        ##Get a frame to serve as the backdrop of UI
        payload = {
        "cameraUuid": self.args.uuid,
        "timestampMs": (self.endTime)*1000#Gets Frame from end of most recent event group
        }
        frameURI = self.session.post(self.url+"video/getExactFrameUri", json = payload)
        if frameURI.status_code != 200:#Check for unexpected status code
            print("Failure to get frameURI (event/getExactFrameUri)")
            return
        frameURI = json.loads(frameURI.text)["frameUri"]

        #Save frame to jpg
        with open("tempFrame.jpg", "wb") as output_fp:
            frame_resp = self.session.get(frameURI)
            output_fp.write(frame_resp.content)
            output_fp.flush()

        window = tkinter.Tk()
        window.title("Double Click to define new areas - Click to Remove")
        window.geometry('1920x1080')
        window.configure(background='grey')

        #Load Image and create canvas
        img = ImageTk.PhotoImage(Image.open('tempFrame.jpg'))
        canvas = tkinter.Canvas(window, width=img.width(), height=img.height(),borderwidth=0, highlightthickness=0)
        canvas.pack(expand=True)
        os.remove('tempFrame.jpg')#Remove frame when done

        draw()
        canvas.bind('<Double-Button-1>', addArea)#On double click
        canvas.bind('<Button-1>', removeArea)#On single click
        canvas.bind('<Motion>', updateSelectRect)#On mouse motion

        window.mainloop()

    def execute(self):
        self.loadAreas()#Load areas for GUI/other actions
        if(self.args.gui):#gui overrides other CLA actions
            self.gui()
        else:
            if(self.args.newArea):
                self.newArea()
            if(self.args.removeArea):
                self.removeArea()

        self.checkAreas()#Report occupied status of areas
        if self.args.dgui:#Display debug GUI
            self.gui()
        return

if __name__ == "__main__":
    engine = isDeskOccupied(sys.argv[1:])
    engine.execute()