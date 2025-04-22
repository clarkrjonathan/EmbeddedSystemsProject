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

        except (ConnectionRefusedError, TimeoutError) as e:
            print(e)
                #pygame.draw.rect(startScreen, buttonInitialColor, button,  0, buttonR)

    #if we make it out the loop no successful connection was made
    q.put(-1)
    return -1



#returns dictionary of all elements on pending screen resized
def resizePendingScreen(width, elements, IPText = "10.49.177.37", portText = "288"):

    pygame.font.init()

    font = "Helvetica"

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

    textFieldScale = 3/4

    portFieldY = height/2
    portFieldX = connectButtonX
    portFieldH = width/16
    portFieldW = connectButtonW

    portTextHeight = portFieldH * textFieldScale

    portTextFontSize = int((portTextHeight/3) * 4)

    portTextX = portFieldX + width/100
    portTextY = (portFieldY + (portFieldH/2) - (portTextHeight/2))-width/75

    
    IPFieldY = (height/2) - portFieldH * 2
    IPFieldX = connectButtonX
    IPFieldH = width/16
    IPFieldW = connectButtonW


    IPTextHeight = IPFieldH * (3/4)
    IPTextFontSize = int((IPTextHeight/3) * 4)
    IPTextY = (IPFieldY + (IPFieldH/2) - (IPTextHeight/2))-width/75
    IPTextX = IPFieldX + width/100




    elements["Radius"] = int(width/100)

    elements["Text"] = pygame.Surface([width, height], pygame.SRCALPHA, 32)

    #add IP Text
    elements["Text"].blit(pygame.font.SysFont(font, IPTextFontSize).render(IPText, True, warmGray), (IPTextX,IPTextY))

    #add Port Text
    elements["Text"].blit(pygame.font.SysFont(font, portTextFontSize).render(portText, True, warmGray), (portTextX,portTextY))


    elements["Port_Field"] = Rect((portFieldX, portFieldY), (portFieldW, portFieldH))
    elements["IP_Field"] = (IPField) = Rect((IPFieldX, IPFieldY), (IPFieldW, IPFieldH))
    elements["Connect_Button"] = Rect((connectButtonX, connectButtonY), (connectButtonW, connectButtonH))
    elements["Cancel_Button"] = Rect((cancelButtonX, cancelButtonY), (cancelButtonW, cancelButtonH))

#draws screen and returns dict of elements for determining collisions
def drawPendingScreen(elements, attemptingConnection, ipField = "10.49.177.37", portField = 288):

    buttonInitialColor = gold
    buttonPendingColor = accentColor2

    elements["Screen"].fill(accentColor1)
    

    #ALL ELEMENTS GO BELOW SCREEN FILL
    #______________________________________


    pygame.draw.rect(elements["Screen"], accentColor2, elements["Cancel_Button"], 0, elements["Radius"])
    pygame.draw.rect(elements["Screen"], white, elements["IP_Field"],0, elements["Radius"])
    pygame.draw.rect(elements["Screen"], white, elements["Port_Field"],0, elements["Radius"])


    if(attemptingConnection):
        #draw pending button
        pygame.draw.rect(elements["Screen"], buttonPendingColor, elements["Connect_Button"], 0, elements["Radius"])
    else:
        #draw idle button
        pygame.draw.rect(elements["Screen"], buttonInitialColor, elements["Connect_Button"], 0, elements["Radius"])

    elements["Screen"].blit(elements["Text"], (0,0))

    

    
    




#loop while pending connection, consists of main screen with ip
#and port fields, and a button to connect which may time out
#if the connection fails and times out then you just stay in that
#screen and keep repeating until valid connection is made
#if at any point during main functions the connection stops we will
#return to this screen with a notification the connection stopped
def pendingConnection():
    cybot_ip = "10.49.178.45"
    cybot_port = 288

    width = 800

    elements = {}
    resizePendingScreen(width, elements)

    img = pygame.image.load('ISULogo.png')
    pygame.display.set_icon(img)
    pygame.display.set_caption("Cybot")


    running = True

    #set true when click start, set false when click cancel
    attemptingConnection = False

    socketConnected = False

    mouse = pygame.mouse.get_pos()

    connectThread = -1
    connectionQueue = queue.Queue()

    client = -1

    

    while(running and (not(socketConnected))):

        drawPendingScreen(elements, attemptingConnection)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:

                #if we clicked button and aren't already attempting, begin connection attempts
                if (elements["Connect_Button"].collidepoint(mouse[0], mouse[1]) and (not(attemptingConnection))):

                    attemptingConnection = True
                    connectThread = threading.Thread(target=connectSocket, args=(cybot_ip, cybot_port, connectionQueue))
                    connectThread.start()
                                       

            if event.type == pygame.VIDEORESIZE:
                # The window was resized, update the screen size
                width = event.size[0]
                resizePendingScreen(width, elements)

        
        mouse = pygame.mouse.get_pos()

        pygame.display.update()


        if(attemptingConnection):
            #visual indicators of attempting connection
            #button color change

            if(not(connectThread.is_alive())):
                #socket either connected or timed out
                connectThread.join()
                client = connectionQueue.get()
                if(client != -1):
                    return client

                #if the thread is not alive we are no longer attempting connection
                attemptingConnection = False


    return client