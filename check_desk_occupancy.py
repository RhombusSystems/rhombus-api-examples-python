from json.decoder import JSONDecodeError
import requests
import argparse
import sys
import json
import time
import os
import tkinter
from PIL import Image, ImageTk

class IsDeskOccupied:

    #Set up workspace for API calls to Rhombus Systems
    def __init__(self,args):
        #Initialize argument parser
        self.argParser = self.__initArgParser()
        self.args = self.argParser.parse_args(args)
        if self.args.dgui:
            self.args.gui == False

        if not self.args.time:
            self.args.time = time.time()
        elif self.args.time > time.time():
            self.args.time = time.time()
        if not self.args.duration:
            self.args.duration = 60
        self.args.time = int(self.args.time)
        self.args.duration = int(self.args.duration)

        #Create a session to set default call Header information
        self.session = requests.session()
        #self.session.headers = {"x-auth-scheme": "api-token","x-auth-apikey": self.args.apiKey}
        self.session.headers = {"x-auth-scheme": "api-token","x-auth-apikey": self.args.apiKey}
        #Set a default base URL for api calls
        self.url = "https://api2.rhombussystems.com/api/"
        self.areas = []#Stores User Defined Areas
        self.humanMovementBounds = []#Stores bounds of Human Movement Events 

        self.img = None
        self.width = None
        self.height = None

    #Define arguments which the user may be prompted for
    @staticmethod
    def __initArgParser():
        argParser = argparse.ArgumentParser(description = 'Determine wether defined workspaces are occupied or not on a camera by camera basis')
        argParser.add_argument("apiKey", help = 'Your personal api key, get this from your Rhombus Console')
        argParser.add_argument("uuid", help = 'UUID of target Camera')
        argParser.add_argument("--time","--t",help = 'Time to check occupancy (Seconds Since Epoch)(Defaults to current time)')
        argParser.add_argument("--duration","--d",help='Duration before time to check for occupancy in seconds (Defaults to 60 seconds)')
        argParser.add_argument("--newArea","--n", help = 'Input a string to define a new area bounding box, must include quotation marks eg: "(0,0)(.5,.2)", coordinates are given as values 0-1.0 in relation to camera resolution')
        argParser.add_argument("--removeArea","--r", help = 'Open a command line menu to remove an area', action = 'store_true')
        argParser.add_argument("--gui",help = 'Opens an image from the target camera and overlays existing areas over it. Draw and delete areas. Overrides concurrent CLA addition and Deletion actions',action = 'store_true')
        argParser.add_argument("--dgui",help = 'Runs check of defined areas then Opens a Debugging GUI which displays motion event bounding boxes alongside user defined areas',action = 'store_true')
        argParser.add_argument("--loadAreas","--l", help = "Name of or path to JSON file containing Areas to load")
        argParser.add_argument("--saveAreas","--s", help = "Name of or path to JSON file to Save Areas to")
        return argParser
    
    #Load user defined areas from uuid.csv
    def setup(self):
        ##Get a camera frame for GUI
        #Must be done even if GUI/DGUI is not selected as the image provides height and width information for camera
        payload = {
        "cameraUuid": self.args.uuid,
        "timestampMs": (self.args.time*1000)
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
        self.img = Image.open('tempFrame.jpg')
        self.width = int(self.img.width)
        self.height = int(self.img.height)

        #If user is loading areas, load areas from JSON
        if self.args.loadAreas:
            try:
                with open(self.args.loadAreas+'.txt') as jsonInput:
                    self.areas=json.load(jsonInput)
            except FileNotFoundError:
                pass#Pass if an error is encountered while loading, self.areas is initialized as [] to still allow user interaction in the event of a failure here
            except JSONDecodeError:
                pass

    #Define a new area and save if user wants
    def newArea(self,newCoords):
        newArea = {
            "posOneX":newCoords[0],
            "posOneY":newCoords[1],
            "posTwoX":newCoords[2],
            "posTwoY":newCoords[3]
        }
        self.areas.append(newArea)
        if self.args.saveAreas:
            with open(self.args.saveAreas+'.txt','w') as jsonOutput:
                json.dump(self.areas,jsonOutput)
        
    #Open a commandline interface to remove an area, and save updated area list to uuid.csv
    def removeArea(self):
        if self.areas == []:
            print("No areas to remove.")
            return
        i = 1
        for area in self.areas:
            area = list(area.values())
            area[0] = float(area[0]) * self.width
            area[1] = float(area[1]) * self.height
            area[2] = float(area[2]) * self.width
            area[3] = float(area[3]) * self.height 
            print("%i : (%i,%i),(%i,%i)"%(i,area[0],area[1],area[2],area[3]))#Print area bounds and associated index
            i+=1

        print("Enter the index of the area to remove:")
        removeMe = int(input())#Take user input
        self.areas.pop(removeMe-1)#Remove specified index from list
        if self.args.saveAreas:
            with open(self.args.saveAreas+'.txt','w') as jsonOutput:
                json.dump(self.areas,jsonOutput)
    
    #Check areas for occupancy
    def checkAreas(self):
        if self.areas == []:
            print("No areas to check.")
            return
        ##Summary
        #Camera UUID, Start Time and Duration -> camera/getFootageBoundingBoxes -> Bounding Box Coords
        #Bounding Box Coords vs. user defined areas -> occupancy
        #For each Area:
            #For each Human Motion Event:
                #if 4 bounds contained: Area Occupied
                #if >=2 bounds contained: Area May Be Occupied
                #Else: Area Not Occupied

        ##Get Recent Bounding Boxes
        payload = {
            "cameraUuid": self.args.uuid,
            "duration": self.args.duration,
            "startTime": self.args.time
        }   
        currentBoundingBoxes = self.session.post(self.url+"camera/getFootageBoundingBoxes",json = payload)
        if currentBoundingBoxes.status_code != 200:#Check for unexpected status code
            print("Failure to get currentEvents (event/getPolicyAlertGroupsForDevice)")
            return
        currentBoundingBoxes = json.loads(currentBoundingBoxes.text)
        currentBoundingBoxes = currentBoundingBoxes["footageBoundingBoxes"]

        for box in currentBoundingBoxes:
            activity = box.get("a")
            if activity == "MOTION_HUMAN":
                #convert event bounds to pixel coordinates and store
                #Convert Permyiads to coordinates -> (value/10000) * total dimension
                left = int((box.get("l")/10000) * self.width)
                right = int((box.get("r")/10000) * self.width)
                top = int((box.get("t")/10000) * self.height)
                bottom = int((box.get("b")/10000) * self.height)
                self.humanMovementBounds.append([left,top,right,bottom,activity])
        ##Compare user defined workspaces to Human Movement Bounding Boxes
        print("\nChecking occupancy as of %i minutes ago" % int((time.time()-self.args.time)/60))
        print("[-1: Area unoccupied | 0: Area may be occupied | 1: Area occupied]\n")
        i = 1
        for area in self.areas:
            #Parse relative values into coordinates
            area = list(area.values())
            area[0] = float(area[0]) * self.width
            area[1] = float(area[1]) * self.height
            area[2] = float(area[2]) * self.width
            area[3] = float(area[3]) * self.height
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
            canvas.create_image(0, 0, image=self.img, anchor=tkinter.NW)#Draw Image on Canvas
            selectRect = canvas.create_rectangle(topx, topy, topx, topy,dash=(2,2), fill='', outline='white')#Draw selectRect
            i = 1
            for area in self.areas:
                #Parse relative values into coordinates
                area = list(area.values())
                area[0] = float(area[0]) * self.width
                area[1] = float(area[1]) * self.height
                area[2] = float(area[2]) * self.width
                area[3] = float(area[3]) * self.height
                if area[0] < area[2]:#Place number identifying area in top left corner
                    canvas.create_text(area[0],area[1],text = str(i),fill = 'green',anchor=tkinter.NW, font=("Arial",25))
                else:
                    canvas.create_text(area[2],area[1],text = str(i),fill = 'green',anchor=tkinter.NW, font=("Arial",25))

                i+=1
                canvas.create_rectangle(area[0], area[1], area[2], area[3], fill='', outline='green',width = 2)#Draw user defined areas
            if self.args.dgui:
                for area in self.humanMovementBounds:
                    if area[4] == "MOTION_HUMAN":
                        canvas.create_rectangle(area[0], area[1], area[2], area[3], fill='',outline='yellow',width = 2)#If in debug mode, draw motion bounds
                    else:
                        canvas.create_rectangle(area[0], area[1], area[2], area[3], fill='',outline='purple',width = 2)#If in debug mode, draw motion bounds

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
                #Parse coordinates into relative values
                newCoords[0]/=self.width
                newCoords[1]/=self.height
                newCoords[2]/=self.width
                newCoords[3]/=self.height

                self.newArea(newCoords)#Add new area

                #Reset selectRect
                topy,topx,boty,botx = 0,0,0,0
                canvas.coords(selectRect, topx, topy, botx, boty)
                #end selecting
                selecting = False
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
                area = list(area.values())
                area[0] *= self.width
                area[1] *= self.height
                area[2] *= self.width
                area[3] *= self.height
                if (area[0] < event.x < area[2]) or (area[2] < event.x < area[0]):#If mouse x pos is in area
                    if (area[1] < event.y < area[3]) or (area[3] < event.y < area[1]):#If mouse y pos is in area
                        self.areas.pop(i)#Remove current index from list, break from loop
                        break
                i-=1
            #write updated list to saveAreas.txt if user wants to save new areas
            if self.args.saveAreas:
                with open(self.args.saveAreas+'.txt','w') as jsonOutput:
                    json.dump(self.areas,jsonOutput)
            draw()#redraw frame
        ###Gui Main
        window = tkinter.Tk()
        window.title("Double Click to define new areas - Click to Remove")
        self.img = ImageTk.PhotoImage(self.img)
        window.geometry(str(self.width)+'x'+str(self.height))
        window.configure(background='grey')

        #create canvas
        canvas = tkinter.Canvas(window, width=self.width, height=self.height,borderwidth=0, highlightthickness=0)
        canvas.pack(expand=True)

        draw()
        canvas.bind('<Double-Button-1>', addArea)#On double click
        canvas.bind('<Button-1>', removeArea)#On single click
        canvas.bind('<Motion>', updateSelectRect)#On mouse motion

        window.mainloop()

    def execute(self):
        self.setup()#Prep predefined areas and get backdrop for UI
        if(self.args.gui):#gui overrides other CLA actions
            self.gui()
        else:
            if(self.args.newArea):
                #Parse the area to add from commandline "(x,y)(x,y)"
                str = self.args.newArea.split(')(')
                newCoords = str[0].split('(')[1].split(',')
                newCoords+=(str[1].split(')')[0].split(','))
                self.newArea(newCoords)
            if(self.args.removeArea):
                self.removeArea()

        self.checkAreas()#Report occupied status of areas
        if self.args.dgui:#Display debug GUI
            self.gui()
        os.remove('tempFrame.jpg')#Remove frame when done
        return

if __name__ == "__main__":
    engine = IsDeskOccupied(sys.argv[1:])
    engine.execute()
