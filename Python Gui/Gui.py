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

#normalizes objects to be within a certain span at a specified offset
def normalizeObjects(objs, windowSurface):
    windowWidth = windowSurface.get_width()
    windowHeight = windowSurface.get_height()

    #measure y span
    #measure x span

    #scale objects size by this too
    if(objs == -1):
        return -1
    
    #copy array
    normalized = [[k for k in x] for x in objs]

    maxR = max([x[0] for x in objs])

    xMin = min([x[1] for x in objs]) - maxR
    xMax = max([x[1] for x in objs]) + maxR
    xSpan = xMax - xMin
    xScale = xSpan/windowWidth


    yMin = min([x[2] for x in objs]) - maxR
    yMax = max([x[2] for x in objs]) + maxR
    ySpan = yMax - yMin
    yScale = ySpan/windowHeight


    if(xScale > yScale):
        for obj in normalized:

            obj[1] -= xMin

            obj[2] -= yMin

            obj[0] /= xScale    
            obj[1]  /= xScale
            obj[2] /= xScale

            obj[2] += (windowHeight/2) - ((ySpan/xScale)/2)


    else:
        for obj in normalized:
            obj[1] -= xMin

            obj[2] -= yMin
            
            obj[0] /= yScale
            obj[1] /= yScale
            obj[2] /= yScale

            obj[1] += (windowWidth/2) - ((xSpan/yScale)/2)



    return normalized


#draws objects onto a window surface that will be rescaled
def drawObjects(objs, window, color = gold):

    if objs == -1:
        return

    for x in objs[1:]:
        pygame.draw.circle(window, color, (x[1], x[2]), x[0])




#returns state if changed, -1 otherwise
def keyDownEventHandler(event, movementStack, currState):
    if(event.key == pygame.K_SPACE):
        movementStack.clear()
        if(currState != "_"):
            return "_"
        else:
            return -1

    if(event.key == pygame.K_w and not("W" in movementStack)):
        movementStack.append("W")

    elif(event.key == pygame.K_s and not("S" in movementStack)):
        movementStack.append("S")
    
    elif(event.key == pygame.K_d and not("D" in movementStack)):
        movementStack.append("D")

    elif(event.key == pygame.K_a and not("A" in movementStack)):
        movementStack.append("A")
    


    if(len(movementStack) > 0):

        if(currState != movementStack[-1]):
            return movementStack[-1]
    

    #the only way to return here is if another key is pressed that doesn't do anything
    return -1

#returns state if changed, -1 otherwise
def keyUpEventHandler(event, movementStack, currState):
    if(len(movementStack) == 0):
        return -1
    
    if(event.key == pygame.K_w):
        movementStack.remove("W")

    elif(event.key == pygame.K_s):
        movementStack.remove("S")
    
    elif(event.key == pygame.K_d):
        movementStack.remove("D")

    elif(event.key == pygame.K_a):
        movementStack.remove("A")

    if(len(movementStack) > 0):

        if(currState != movementStack[-1]):
            #picked up end key
            return movementStack[-1]
        
    #state should be idle
    elif(currState != "I"):
        #picked up last key
        return "I"

    return -1

def drawCybot(window, cybotSprite, color = (255, 0, 0)):
    #we have angle to draw
    if(len(cybotSprite) > 3):
        pygame.draw.circle(window, color, (cybotSprite[1], cybotSprite[2]), cybotSprite[0])

        frontDotSize = cybotSprite[0]/5

        xOffset = math.cos((cybotSprite[3]) * (math.pi/180)) * (cybotSprite[0] - frontDotSize)
        yOffset = math.sin((cybotSprite[3]) * (math.pi/180)) * (cybotSprite[0] - frontDotSize)

        pygame.draw.circle(window, (0,0,0), (cybotSprite[1] + xOffset, cybotSprite[2] + yOffset), frontDotSize)
    elif(len(cybotSprite) == 3):
        #can still draw just no front
        pygame.draw.circle(window, color, (cybotSprite[1], cybotSprite[2]), cybotSprite[0])
    else:
        print("Cannot Draw cybot")

def updateField(window, objs):
    window.fill((0,0,0,0))
    drawObjects(objs, window)
    drawCybot(window, objs[0])

#inverts on y axis
def invertObjects(objs):
    if(objs == -1):
        return

    objs[0][3] += 180
    for x in objs:
        x[2] = x[2] * -1


#This is where all sizes of elements will be configured, except for things within the window which are a seperate surface and just scale to the window box
#also called every time the display is resized
def constructScreen(width, elements, state):
    height = (width * 9)/16

    windowWidth = width * (3/5)
    windowHeight = height * (3/5)

    windowXOffset = (width - windowWidth)/2
    windowYOffset = ((height - windowHeight)/2) - height/10

    fieldTabHeight = width/40
    fieldTabWidth = width/20
    fieldTabX = windowWidth/30

    elements["Field_Tab"] = Rect((windowXOffset + fieldTabX, windowYOffset - fieldTabHeight + 3) , (fieldTabWidth, fieldTabHeight))
    elements["Scan_Tab"] = Rect((windowXOffset + fieldTabX + fieldTabWidth, windowYOffset - fieldTabHeight + 3) , (fieldTabWidth, fieldTabHeight))

    elements["Screen"] = pygame.display.set_mode((width, height), pygame.RESIZABLE)
    elements["Window_Rect"] = Rect((windowXOffset, windowYOffset) , (windowWidth, windowHeight))

def writeOnRect(screen, rect, text, color, font="Helvetica", fontSize = 100):
    screen.blit(pygame.transform.scale(pygame.font.SysFont(font, fontSize).render(text, True, color), (rect.width, rect.height)), (rect.x, rect.y))


def getIRDist(rawIR):
    if(rawIR == 0):
        raise ValueError

    exp = -0.54574863529
    a = 9561.29245589

    x = rawIR/a
    y = 1/exp


    dist = math.pow(x, y)

    return dist

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

#actually draws elements on the screen
def drawScreen(elements, state):
    #keep in mind state determines which elements are displayed, constructing them basically just resizes
    pygame.font.init()

    font = "Helvetica"

    windowColor = accentColor1
    #draw elements
    #based on state 
    elements["Screen"].fill(darkRed)
    

    
    fieldTabColor = windowColor if state["Window_Tab"] == "Field" else warmGray
    scanTabColor = windowColor if state["Window_Tab"] == "Scan" else warmGray
    
    pygame.draw.rect(elements["Screen"], scanTabColor, elements["Scan_Tab"], border_top_left_radius=int(elements["Field_Tab"].x/30),border_top_right_radius=int(elements["Field_Tab"].x/30))
    pygame.draw.rect(elements["Screen"], fieldTabColor, elements["Field_Tab"], border_top_left_radius=int(elements["Field_Tab"].x/30),border_top_right_radius=int(elements["Field_Tab"].x/30))


    writeOnRect(elements["Screen"], elements["Scan_Tab"], "Scan", darkRed)
    writeOnRect(elements["Screen"], elements["Field_Tab"], "Field", darkRed)

    pygame.draw.rect(elements["Screen"], windowColor, elements["Window_Rect"], border_radius=int(elements["Window_Rect"].x/20))

    if(state["Window_Tab"] == "Field"):
        elements["Screen"].blit(pygame.transform.scale(elements["Field_Surface"], (elements["Window_Rect"].width, elements["Window_Rect"].height)), (elements["Window_Rect"].x,elements["Window_Rect"].y))
        fieldTabColor = windowColor
    elif(state["Window_Tab"] == "Scan"):
        elements["Screen"].blit(pygame.transform.scale(elements["Scan_Surface"], (elements["Window_Rect"].width, elements["Window_Rect"].height)), (elements["Window_Rect"].x,elements["Window_Rect"].y))
        scanTabColor = windowColor

    pygame.display.update()


#objects x, y, size(radius for circle, edge for square, either way can be linearly scaled), type stored in currField

def main():

    pygame.init()

    client, width = pending.pendingConnection()

    elements = {}
    state = {"Window_Tab" : ""}
    
    #true if client valid
    running = client != -1

    #making a field surface the same size as the screen which will be projected into the inner window
    elements["Field_Surface"] = pygame.Surface([width, (width * 9)/16], pygame.SRCALPHA, 32)
    elements["Scan_Surface"] = pygame.Surface([width, (width * 9)/16], pygame.SRCALPHA, 32)


    pygame.display.set_caption("Hello Pygame")
    pygame.display.update()


    message = ""
    currField = -1
    objColor = gold
    movementStack = []

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
            
            elif event.type == pygame.KEYDOWN:
                newState = keyDownEventHandler(event, movementStack, currState)
                

            elif event.type == pygame.KEYUP:
                newState = keyUpEventHandler(event, movementStack, currState)

            #change in state
            if (newState != -1):
                currState = newState
                #print(currState)
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
            
                if(message[0:6] == "Field:"):
                    #redraw the field

                    rawObjects = parseObjects(message)

                    objects = normalizeObjects(rawObjects, elements["Field_Surface"])
                    updateField(elements["Field_Surface"], objects)

                elif(message[0:5] == "Scan:"):
                    scanData = parseObjects(message)
                    graphScan(elements["Scan_Surface"], scanData)
                    print(message)
                
                elif(message[0:13] == "IR Calibrate:"):
                    with open ("IRCalibrationData.csv", "a") as file:
                        file.write(message)

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
    


main()