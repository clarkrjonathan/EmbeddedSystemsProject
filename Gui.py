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
def normalizeObjects(objs, windowWidth = 1600, windowHeight = 900, windowXOffset = 0, windowYOffset = 0):

    #measure y span
    #measure x span

    #find x scale to bring largest x back into buffer keeping in mind radius
    #find y scale t bring largest y into buffer keeping in mind radius
    #pick the scale thats smallest as the entire scale

    #this scale gives us a size scale, now we have to find offset to center it in the window

    #based on dimension scaling from for example y
    #subtract minimum of y from all y vals
    #this will put the minimum y on the top (because pygame draws top to bottom) and the maximum on the bottom

    #subtract minimum x value from all x vals
    #add half of windows x width - half of x span

    #scale objects size by this too
    if(objs == -1):
        return -1
    
    print(objs)
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

            obj[1] += windowXOffset
            obj[2] += windowYOffset

    else:
        for obj in normalized:
            obj[1] -= xMin

            obj[2] -= yMin
            
            obj[0] /= yScale
            obj[1] /= yScale
            obj[2] /= yScale

            obj[1] += (windowWidth/2) - ((xSpan/yScale)/2)

            obj[1] += windowXOffset
            obj[2] += windowYOffset


    print(normalized)

    return normalized

def drawObjects(objs, screen, color = gold):

    if objs == -1:
        return

    for x in objs[1:]:
        pygame.draw.circle(screen, color, (x[1], x[2]), x[0])




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

def drawCybot(screen, cybotSprite, color = (255, 0, 0)):
    #we have angle to draw
    if(len(cybotSprite) > 3):
        pygame.draw.circle(screen, color, (cybotSprite[1], cybotSprite[2]), cybotSprite[0])

        frontDotSize = cybotSprite[0]/5

        xOffset = math.cos(cybotSprite[3] * (math.pi/180)) * (cybotSprite[0] - frontDotSize)
        yOffset = math.sin(cybotSprite[3] * (math.pi/180)) * (cybotSprite[0] - frontDotSize)

        pygame.draw.circle(screen, (0,0,0), (cybotSprite[1] + xOffset, cybotSprite[2] + yOffset), frontDotSize)
    elif(len(cybotSprite) == 3):
        #can still draw just no front
        pygame.draw.circle(screen, color, (cybotSprite[1], cybotSprite[2]), cybotSprite[0])
    else:
        print("Cannot Draw cybot")

#inverts on y axis
def invertObjects(objs):
    if(objs == -1):
        return

    objs[0][3] += 180
    for x in objs:
        x[2] = x[2] * -1


def main():

    pygame.init()

    client = pending.pendingConnection()
    
    #true if client valid
    running = client != -1

    screen = pygame.display.set_mode((1600, 900))


    pygame.display.set_caption("Hello Pygame")
    pygame.display.update()


    message = ""
    currField = -1
    objColor = gold
    movementStack = []

    windowWidth = 1000
    windowHeight = 500

    windowXOffset = (screen.get_width() - windowWidth)/2

    windowYOffset = ((screen.get_height() - windowHeight)/2) - screen.get_height()/10

    windowBuffer = 30

    #cybot for visual data, [size, x, y, angle]
    cybotSprite = [0,0,0,0]

    #started Idle
    #I = Idle
    #W = Foward
    #S = Back
    #D = Rotate Right
    #A = Rotate Left
    #_ = Scan
    #cybot gets one command sent per change of action with an Idle signal between
    currState = "I"


    while (running and (message != "end")):
        message = ""
        screen.fill(accentColor3)

        pygame.draw.rect(screen, accentColor1, Rect((windowXOffset - windowBuffer/2, windowYOffset - windowBuffer/2), (windowWidth + windowBuffer, windowHeight + windowBuffer)), 0, 3)
        drawObjects(currField, screen, objColor)
        drawCybot(screen ,cybotSprite)

        pygame.display.update()
        
        #websocket duty cycle
        for event in pygame.event.get():
            newState = -1

            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                newState = keyDownEventHandler(event, movementStack, currState)
                

            elif event.type == pygame.KEYUP:
                newState = keyUpEventHandler(event, movementStack, currState)

            #change in state
            if (newState != -1):
                currState = newState
                print(currState)
                client.send(currState.encode())          

        
        try:
            if(check_socket_data(client)):
                    data = client.recv(1)
            else:
                data = b'\x00'


            #we have received data and now can get information about it
            if(data == b'\x06'):
                message = recvString(client)
            
                if(message[0:6] == "Field:"):

                    client.send(b"Received Field\n")
                    pygame.display.set_caption("Current Field")
                    rawObjects = parseObjects(message)

                    invertObjects(rawObjects)
                    objects = normalizeObjects(rawObjects, windowWidth, windowHeight, windowXOffset, windowYOffset)

                    cybotSprite = objects[0]
                    currField = objects[1:]


                else:
                    print("Message: " + message)
                
        except (ConnectionResetError):
            client = pending.pendingConnection()
            if(client == -1):
                running = False
            
            screen = pygame.display.set_mode((1600, 900))



        #termination of pygame
        


    pygame.quit()
    


main()