import socket
import time
import pygame
from pygame.locals import *
import select
import math
import threading
import queue
from ISUColors import *


def connectSocket(cybot_ip, cybot_port, q):
    maxAttempts = 1

    #try to establish connection

    for i in range(maxAttempts):
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((cybot_ip, cybot_port))
            q.put(client)
            
            return client
            #pygame.draw.rect(startScreen, (0,255,0), button,  0, buttonR)
        except (socket.gaierror) as e:
            print("Invalid IP/Port Field")
            print(e)
            q.put(-1)
            return -1

        except (ConnectionRefusedError, TimeoutError) as e:
            print(e)
                #pygame.draw.rect(startScreen, buttonInitialColor, button,  0, buttonR)
        

    #if we make it out the loop no successful connection was made
    q.put(-1)
    return -1



#returns dictionary of all elements on pending screen resized
def resizePendingScreen(width, elements):

    pygame.font.init()

    

    height = (width * 9)/16
    elements["Screen"] = pygame.display.set_mode((width, height), pygame.RESIZABLE)

    connectButtonX = (width/10)
    connectButtonY = (height/2) + height/4
    connectButtonW = width/1.75
    connectButtonH = height/5
    
    cancelButtonY = connectButtonY
    cancelButtonW = connectButtonW/3
    cancelButtonH = connectButtonH
    cancelButtonX = width - (connectButtonX + cancelButtonW) 

    portFieldY = height/2
    portFieldX = connectButtonX
    portFieldH = width/16
    portFieldW = connectButtonW

    

    
    IPFieldY = (height/2) - portFieldH * 2
    IPFieldX = connectButtonX
    IPFieldH = width/16
    IPFieldW = connectButtonW


    elements["Radius"] = int(width/100)

    elements["Port_Field"] = Rect((portFieldX, portFieldY), (portFieldW, portFieldH))
    elements["IP_Field"] = (IPField) = Rect((IPFieldX, IPFieldY), (IPFieldW, IPFieldH))
    elements["Connect_Button"] = Rect((connectButtonX, connectButtonY), (connectButtonW, connectButtonH))
    elements["Cancel_Button"] = Rect((cancelButtonX, cancelButtonY), (cancelButtonW, cancelButtonH))

#maps text to rectangle based on some sizing and offset parameters, needs surface width to offset onto rect
#returns tuple of (textX, textY, fontsize)
def putTextOnRect(rect, textFieldScale = (3/4), xOffset = 4, yOffset = 4):

    textHeight = rect.height * textFieldScale

    #literals shouldnt be changed they scale the font size to the textHeight
    textFontSize = int((textHeight/3) * 4)

    textX = rect.x + textHeight/xOffset
    textY = rect.y + (rect.height/2) - (textHeight/2) - (textHeight/yOffset)

    return (textX, textY, textFontSize)

def drawText(elements, state, defaultIPText, defaultPortText, font = "Helvetica"):

    
    if(len(state["IP_Text"]) > 0):
        IPText = state["IP_Text"]
        IPTextColor = black
    else:
        IPText = defaultIPText
        IPTextColor = warmGray

    if(len(state["Port_Text"]) > 0):
        portText = state["Port_Text"]
        portTextColor = black
    else:
        portText = defaultPortText
        portTextColor = warmGray

    width = elements["Screen"].get_width()
    height = elements["Screen"].get_height()


    elements["Text"] = pygame.Surface([width, height], pygame.SRCALPHA, 32)

    #add connectButton label
    if(state["Attempting_Connection"]):
        connectText = "Connecting"
        connectTextX, connectTextY, connectTextFontSize =  putTextOnRect(elements["Connect_Button"], textFieldScale = 1/2)
    else:
        connectText = "Connect"
        connectTextX, connectTextY, connectTextFontSize =  putTextOnRect(elements["Connect_Button"])

    elements["Text"].blit(pygame.font.SysFont(font, connectTextFontSize).render(connectText, True, warmGray), (connectTextX,connectTextY))

    cancelText = "Cancel"
    cancelTextX, cancelTextY, cancelTextFontSize = putTextOnRect(elements["Cancel_Button"], textFieldScale = 1/3)
    elements["Text"].blit(pygame.font.SysFont(font, cancelTextFontSize).render(cancelText, True, warmGray), (cancelTextX, cancelTextY))


    #add Port text
    portTextX, portTextY, portTextFontSize = putTextOnRect(elements["Port_Field"])
    elements["Text"].blit(pygame.font.SysFont(font, portTextFontSize).render(portText, True, portTextColor), (portTextX,portTextY))

    #add IP text
    IPTextX, IPTextY, IPTextFontSize = putTextOnRect(elements["IP_Field"])
    elements["Text"].blit(pygame.font.SysFont(font, IPTextFontSize).render(IPText, True, IPTextColor), (IPTextX,IPTextY))

    elements["Screen"].blit(elements["Text"], (0,0))

#draws screen and returns dict of elements for determining collisions
def drawPendingScreen(elements, state, defaultIPText, defaultPortText):

    buttonInitialColor = gold
    buttonPendingColor = accentColor2

    elements["Screen"].fill(accentColor1)
    

    #         ALL ELEMENTS GO BELOW SCREEN FILL
    ########################################################


    pygame.draw.rect(elements["Screen"], accentColor2, elements["Cancel_Button"], 0, elements["Radius"])
    pygame.draw.rect(elements["Screen"], white, elements["IP_Field"],0, elements["Radius"])
    pygame.draw.rect(elements["Screen"], white, elements["Port_Field"],0, elements["Radius"])


    if(state["Attempting_Connection"]):
        #draw pending button
        pygame.draw.rect(elements["Screen"], buttonPendingColor, elements["Connect_Button"], 0, elements["Radius"])
    else:
        #draw idle button
        pygame.draw.rect(elements["Screen"], buttonInitialColor, elements["Connect_Button"], 0, elements["Radius"])

    drawText(elements, state, defaultIPText, defaultPortText)



#loop while pending connection, consists of main screen with ip
#and port fields, and a button to connect which may time out
#if the connection fails and times out then you just stay in that
#screen and keep repeating until valid connection is made
#if at any point during main functions the connection stops we will
#return to this screen with a notification the connection stopped
def pendingConnection():

    with open("SocketInfo.txt", "r") as file:
        defaultIPText = file.readline().strip()
        defaultPortText = file.readline().strip()


    width = 800

    elements = {}
    state = {"Attempting_Connection" : False, "Socket_Connected" : False, "In_IPField" : False, "In_PortField" : False, "IP_Text" : "", "Port_Text" : ""}

    resizePendingScreen(width, elements)
    
    

    img = pygame.image.load('ISULogo.png')
    pygame.display.set_icon(img)
    pygame.display.set_caption("Cybot")


    running = True

    mouse = pygame.mouse.get_pos()

    connectThread = -1
    connectionQueue = queue.Queue()

    client = -1

    

    while(running and (not(state["Socket_Connected"]))):

        drawPendingScreen(elements, state, defaultIPText, defaultPortText)
        mouse = pygame.mouse.get_pos()
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:

                #if we clicked button and aren't already attempting, begin connection attempts
                if (elements["Connect_Button"].collidepoint(mouse[0], mouse[1]) and (not(state["Attempting_Connection"]))):

                    
                    cybot_ip = state["IP_Text"] if len(state["IP_Text"])> 0 else defaultIPText
                    cybot_port = state["Port_Text"] if len(state["Port_Text"]) > 0 else defaultPortText

                    try:
                        connectThread = threading.Thread(target=connectSocket, args=(cybot_ip, int(cybot_port), connectionQueue))
                        connectThread.start()
                        state["Attempting_Connection"]  = True

                    except ValueError as e:
                        print(e)

                if (elements["Cancel_Button"].collidepoint(mouse[0], mouse[1]) and state["Attempting_Connection"]):

                    state["Attempting_Connection"] = False
                    connectThread = -1
                
                if(elements["Port_Field"].collidepoint(mouse[0], mouse[1])):
                    state["In_PortField"] = True
                else:
                    #make sure if we clicked somewhere not inside the field, we are not in the field
                    state["In_PortField"] = False

                if(elements["IP_Field"].collidepoint(mouse[0], mouse[1])):
                    state["In_IPField"] = True
                else:
                    state["In_IPField"] = False

            if event.type == pygame.KEYDOWN:

                if(state["In_IPField"]):

                    #start saving keystrokes 
                    if(event.key == pygame.K_BACKSPACE):
                        if(len(state["IP_Text"]) > 0):
                            state["IP_Text"] = state["IP_Text"][:-1]
                    else:
                        state["IP_Text"] += event.unicode
                    
                
                if(state["In_PortField"]):

                    #start saving port
                    if(event.key == pygame.K_BACKSPACE):
                        if(len(state["Port_Text"]) > 0):
                            state["Port_Text"] = state["Port_Text"][:-1]
                    else:
                        state["Port_Text"] += event.unicode
                    

                                    

            if event.type == pygame.VIDEORESIZE:
                # The window was resized, update the screen size
                width = event.size[0]
                resizePendingScreen(width, elements)



        if(state["Attempting_Connection"]):
            #visual indicators of attempting connection
            #button color change

            if(not(connectThread.is_alive())):
                #socket either connected or timed out
                connectThread.join()
                client = connectionQueue.get()
                
                if(client != -1):

                    #socket is connected and save connection info as default
                    with open("SocketInfo.txt", "w") as file:

                        if(len(state["IP_Text"].strip()) > 0):
                            file.write(state["IP_Text"] + "\n")
                        else:
                            file.write(defaultIPText + "\n")

                        if(len(state["Port_Text"].strip()) > 0):

                            file.write(state["Port_Text"] + "\n")
                        else:
                            file.write(defaultPortText + "\n")

                    return (client, width)

                #if the thread is not alive we are no longer attempting connection
                state["Attempting_Connection"] = False


    return (client, width)