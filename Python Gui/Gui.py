import socket
import time
import pygame
from pygame.locals import *
import select
import math
import threading
import queue
import pending
from ISUColors import *
import datetime
import os
import cmath
from screen import *
from field import *


def check_socket_data(sock):
    sock.setblocking(0)

    try:
        data = sock.recv(1, socket.MSG_PEEK)
        hasData = True
    except BlockingIOError:
        hasData = False
    sock.setblocking(1)

    return hasData

def recvString(client):
    byte = client.recv(1)
    message = ""

    while(byte != b'\x00'):
        message += byte.decode()
        byte = client.recv(1)
    
    return message 



#may need to add some sort of stop message if I can't send the whole field in one but I should be able to
def parseObjects(message):
    objStrings = message.splitlines()[1:]
    objs = [[float(k) for k in x.split(", ")] for x in objStrings]
    return objs

#draws objects onto a window surface that will be rescaled
def drawObjects(objs, window, color = gold):

    if objs == -1:
        return

    for x in objs[1:]:
        pygame.draw.circle(window, color, (x[0], x[1]), x[2])


def trackBumpObject(bumpObjects, cybotSprite, scale):
    rockRadius = 75
    rockColor = (155, 155, 155)

    xOffset = math.cos((cybotSprite[2]) * (math.pi/180)) * (185 + rockRadius) 
    yOffset = math.sin((cybotSprite[2]) * (math.pi/180)) * (185 + rockRadius)

    x = cybotSprite[0] + xOffset
    y = cybotSprite[1] + yOffset

    scale["xMax"] = scale["xMax"] if x < scale["xMax"] else x
    scale["xMin"] = x if x < scale["xMin"] else scale["xMin"]

    scale["yMax"] = y if y > scale["yMax"] else scale["yMax"]
    scale["yMin"] = y if y < scale["yMin"] else scale["yMin"]

    bumpObjects.append([x, y, rockRadius, rockColor])


def getIRDist(rawIR):
    if(rawIR == 0):
        raise ValueError

    exp = -0.54574863529
    a = 9561.29245589

    x = rawIR/a
    y = 1/exp


    dist = math.pow(x, y)

    return dist

def checkDistSquared(pointA, pointB):
    return ((pointA[0] - pointB[0])**2) * ((pointA[1]-pointB[1])**2)

#scan data comes in as irRaw, irDist, pingDist, angle
def graphScan(window, scanData, graphIRRaw = True, graphIRDist = True, graphPing = True, normalizeRawIR = True, xMin=0, xMax=180, yMin = 0, yMax = 200):
    window.fill((0,0,0,0))


    #what to multiply x by
    xScale = window.get_width()/(xMax - xMin)
    yScale = window.get_height()/(yMax - yMin)

    pointSize = window.get_width()/120

    IRRawColor = (230, 0, 0)
    IRDistColor = (0,230,0)
    pingDistColor = (0,0,230)

    #copy and scale array
    if(normalizeRawIR):
        scaledData = [[(getIRDist(y[0])  * yScale) + yMin,(y[1] * yScale) + yMin, (y[2] * yScale) + yMin, (y[3] * xScale) + xMin] for y in scanData]
    else:
        scaledData = [[(y[0]  * yScale) + yMin,(y[1] * yScale) + yMin, (y[2] * yScale) + yMin, (y[3] * xScale) + xMin] for y in scanData]

    for point in scaledData:
        
        if(graphIRRaw):
            pygame.draw.circle(window, IRRawColor, (point[3], window.get_height() - point[0]), pointSize)
        if(graphIRDist):
            pygame.draw.circle(window, IRDistColor, (point[3], window.get_height() - point[1]), pointSize)
        if(graphPing):
            pygame.draw.circle(window, pingDistColor, (point[3], window.get_height() - point[2]), pointSize)

def zoom(scale, cybot):
    cybot[2] = cybot[2] % 360

    #pointing positive x
    if(cybot[2] > 315 or cybot[2] < 45):
        scale["xMin"] = cybot[0]
        scale["xMax"] = cybot[0] + 1000
        scale["yMin"] = cybot[1] - 300
        scale["yMax"] = cybot[1] + 300
    #pointing positive y
    elif(cybot[2] > 45 and cybot[2] < 135):
        scale["xMin"] = cybot[0] - 300
        scale["xMax"] = cybot[0] + 300
        scale["yMin"] = cybot[1]
        scale["yMax"] = cybot[1] + 1000
    #pointing negative x
    elif(cybot[2] > 135 and cybot[2] < 225):
        scale["xMin"] = cybot[0] - 1000
        scale["xMax"] = cybot[0]
        scale["yMin"] = cybot[1] - 300
        scale["yMax"] = cybot[1] + 300
    #pointing negative y
    elif(cybot[2] > 225 and cybot[2] < 315):
        scale["xMin"] = cybot[0] - 300
        scale["xMax"] = cybot[0] + 300
        scale["yMin"] = cybot[1] - 1000
        scale["yMax"] = cybot[1]


#objects x, y, size(radius for circle, edge for square, either way can be linearly scaled), type stored in currField

def main():

    pygame.init()

    client, width = pending.pendingConnection()

    elements = {}
    state = {"Window_Tab" : ""}
    state["FirstScan"] = True
    
    #true if client valid
    running = client != -1

    #making a field surface the same size as the screen which will be projected into the inner window
    elements["Field_Surface"] = pygame.Surface([width, (width * 9)/16], pygame.SRCALPHA, 32)
    elements["Scan_Surface"] = pygame.Surface([width, (width * 9)/16], pygame.SRCALPHA, 32)

    #list of multiple scans, every time there is a new object list it will be appended
    #this always will be the raw data straight from cybot meaning the absolute positions in the room of points
    fieldScansIR = []

    fieldScansPing = []

    otherObjects = []

    #values needed to scale any object to fit within other boundaries
    scale = {"xMin" : 0, "xMax" : 500, "yMin" : 0, "yMax" : 500}

    pygame.display.set_caption("Hello Pygame")
    pygame.display.update()


    message = ""
    currField = -1
    objColor = gold
    movementStack = []

    cybot = [0,0,0]
    

    logFolder = "Logs/" + datetime.datetime.now().strftime("%m-%d-%Y")

    if (not(os.path.isdir("Logs"))):
        os.mkdir("Logs")

    if (not(os.path.isdir(logFolder))):
        os.mkdir(logFolder)


    #start logs
    logFileName = logFolder + "/log_" + datetime.datetime.now().strftime("%m-%d-%Y_%H-%M-%S") + ".txt"

    #started Idle
    #I = Idle
    #W = Foward
    #S = Back
    #D = Rotate Right
    #A = Rotate Left
    #_ = Scan
    #cybot gets one command sent per change of action with an Idle signal between
    currState = "I"

    constructScreen(width, elements, state)

    while (running and (message != "end")):

        #draw screen background
        #draw elements like buttons window inlay etc
        #based on state call the specific tab draw function
        #blit that scaled result to the screen

        #on a resize, only the important elements like buttons and window size need to be resized not every little object or line on a graph or text in the console
        
        message = ""

        drawScreen(elements, state)

        
        #websocket duty cycle
        for event in pygame.event.get():
            newState = -1

            if event.type == pygame.QUIT:
                running = False
            
            mouse = pygame.mouse.get_pos()

            if event.type == pygame.MOUSEBUTTONDOWN:


                if(elements["Field_Tab"].collidepoint(mouse[0], mouse[1])):

                    state["Window_Tab"] = "Field"
                elif(elements["Scan_Tab"].collidepoint(mouse[0], mouse[1])):

                    state["Window_Tab"] = "Scan"
                elif(elements["Trim_Plus"].collidepoint(mouse[0], mouse[1])):
                    trim = "R"
                    client.send(trim.encode())
                elif(elements["Trim_Minus"].collidepoint(mouse[0], mouse[1])):
                    trim = "L"
                    client.send(trim.encode())
                elif(elements["Place_Rock"].collidepoint(mouse[0], mouse[1])):
                    trackBumpObject(otherObjects, cybot, scale)
                    
            
            elif event.type == pygame.KEYDOWN:
                newState = keyDownEventHandler(event, movementStack, currState)
                if(event.key == pygame.K_f):
                    message = "F"
                    client.send(message.encode())
                

            elif event.type == pygame.KEYUP:
                newState = keyUpEventHandler(event, movementStack, currState)
                if (event.key == pygame.K_LSHIFT):

                    if(len(otherObjects)>0):
                        updateScale(otherObjects, scale, state["FirstScan"])
                    for scan in fieldScansIR:
                        updateScale(scan, scale, state["FirstScan"])

            #change in state
            if (newState != -1):
                currState = newState

                client.send(currState.encode())    
            

            if event.type == pygame.VIDEORESIZE:
                # The window was resized, update the screen size
                width = event.size[0]
                constructScreen(width, elements, state)
                
                
                
        
        try:
            if(check_socket_data(client)):
                    data = client.recv(1)
            else:
                data = b'\x00'


            #we have received data and now can get information about it
            if(data == b'\x06'):
                message = recvString(client)
            
                if(message[0:10] == "IR Points:"):
                    #redraw the field

                    rawObjects = parseObjects(message)
                    if(state["FirstScan"]):
                        state["FirstScan"]= False
                    
                    fieldScansIR.append(rawObjects)

                    #don't bother updating the field here because the field will be updated when we receive the cybot position and will just be overwritten
                    #all we need to do here is add points to fieldScan and update our scale which could end up just being overridden by the cybot
                    updateScale(rawObjects, scale, state["FirstScan"])
                
                elif(message[0:12] == "Ping Points:"):
                    
                    rawObjects = parseObjects(message)
                    
                    fieldScansPing.append(rawObjects)


                elif(message[0:5] == "Scan:"):
                    scanData = parseObjects(message)
                    graphScan(elements["Scan_Surface"], scanData)
                    print(message)
                
                elif(message[0:13] == "IR Calibrate:"):
                    with open ("IRCalibrationData.csv", "a") as file:
                        file.write(message)

                #cybot sent its position as x, y, angle
                elif(message[0:9] == "Position:"):
                    #save cybot position
                    cybot = [float(x) for x in message.splitlines()[1].split(", ")]

                    #check if pressing shift to zoom
                    pressed = pygame.key.get_pressed()
                    if(pressed[pygame.K_LSHIFT]):
                        zoom(scale, cybot)
                    else:
                        #update scaling if cybot is outside window
                        if(cybot[0] < scale["xMin"]):
                            scale["xMin"] = cybot[0]
                        elif(cybot[0] > scale["xMax"]):
                            scale["xMax"] = cybot[0]
                        
                        if(cybot[1]  < scale["yMin"]):
                            scale["yMin"] = cybot[1]
                        elif (cybot[1] > scale["yMax"]):
                            scale["yMax"] = cybot[1]
                    
                    updateField(elements["Field_Surface"], fieldScansIR, fieldScansPing, cybot, scale, otherObjects)

                    
                
                #cybot is telling the gui to force idle
                elif(message == "I"):
                    #clearing movement stack ensures we don't accidentally keep moving
                    #may want to block movement for like half a second but I think that would be easier to do on the cybot side
                    movementStack.clear()
                    currState = "I"

                else:
                    print("Cybot: " + message)
                
                with open(logFileName, "a") as file:
                    file.write(message)
                
        except (ConnectionResetError):
            client, width = pending.pendingConnection()
            if(client == -1):
                running = False
            



        #termination of pygame
        


    pygame.quit()
    

if __name__ == "__main__":
    main()