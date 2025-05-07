import socket
import time
import pygame
from pygame.locals import *
import select
import math
import threading
import queue
from ISUColors import *
import datetime
import os
import cmath

#General gui handling



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
    
    try:
        if(event.key == pygame.K_w):
            movementStack.remove("W")

        elif(event.key == pygame.K_s):
            movementStack.remove("S")
    
        elif(event.key == pygame.K_d):
            movementStack.remove("D")

        elif(event.key == pygame.K_a):
            movementStack.remove("A")
    except:
        pass
    

    if(len(movementStack) > 0):

        if(currState != movementStack[-1]):
            #picked up end key
            return movementStack[-1]
        
    #state should be idle
    elif(currState != "I"):
        #picked up last key
        return "I"

    return -1

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

    
    trimButtonWidth = width/10
    trimButtonHeight = width/20
    trimButtonX = width/15
    trimButtonY = height/2 - trimButtonHeight

    elements["Trim_Plus"] = Rect((trimButtonX, trimButtonY), (trimButtonWidth, trimButtonHeight))
    elements["Trim_Minus"] = Rect((trimButtonX, trimButtonY + (4 * trimButtonHeight)/3), (trimButtonWidth, trimButtonHeight))

    placeRockWidth = width/15
    placeRockHeight = width/20

    placeRockX = width - width/15 - placeRockWidth
    placeRockY = height/2 - placeRockHeight

    elements["Place_Rock"] = Rect((placeRockX, placeRockY), (placeRockWidth, placeRockHeight))

def writeOnRect(screen, rect, text, color, font="Helvetica", fontSize = 100):
    screen.blit(pygame.transform.scale(pygame.font.SysFont(font, fontSize).render(text, True, color), (rect.width, rect.height)), (rect.x, rect.y))

#actually draws elements on the screen
def drawScreen(elements, state):
    #keep in mind state determines which elements are displayed, constructing them basically just resizes
    pygame.font.init()

    font = "Helvetica"

    windowColor = (0,0,0)
    #draw elements
    #based on state 
    elements["Screen"].fill(darkRed)
    

    
    fieldTabColor = windowColor if state["Window_Tab"] == "Field" else warmGray
    scanTabColor = windowColor if state["Window_Tab"] == "Scan" else warmGray
    
    pygame.draw.rect(elements["Screen"], scanTabColor, elements["Scan_Tab"], border_top_left_radius=int(elements["Field_Tab"].x/30),border_top_right_radius=int(elements["Field_Tab"].x/30))
    pygame.draw.rect(elements["Screen"], fieldTabColor, elements["Field_Tab"], border_top_left_radius=int(elements["Field_Tab"].x/30),border_top_right_radius=int(elements["Field_Tab"].x/30))
    
    pygame.draw.rect(elements["Screen"], warmGray, elements["Trim_Plus"])
    pygame.draw.rect(elements["Screen"], warmGray, elements["Trim_Minus"])
    pygame.draw.rect(elements["Screen"], warmGray, elements["Place_Rock"])

    writeOnRect(elements["Screen"], elements["Trim_Plus"], "Right Trim", black)
    writeOnRect(elements["Screen"], elements["Trim_Minus"], "Left Trim", black)

    writeOnRect(elements["Screen"], elements["Scan_Tab"], "Scan", darkRed)
    writeOnRect(elements["Screen"], elements["Field_Tab"], "Field", darkRed)
    
    writeOnRect(elements["Screen"], elements["Place_Rock"], "Rock", black)



    pygame.draw.rect(elements["Screen"], windowColor, elements["Window_Rect"], border_radius=int(elements["Window_Rect"].x/20))

    if(state["Window_Tab"] == "Field"):
        elements["Screen"].blit(pygame.transform.scale(elements["Field_Surface"], (elements["Window_Rect"].width, elements["Window_Rect"].height)), (elements["Window_Rect"].x,elements["Window_Rect"].y))
        fieldTabColor = windowColor
    elif(state["Window_Tab"] == "Scan"):
        elements["Screen"].blit(pygame.transform.scale(elements["Scan_Surface"], (elements["Window_Rect"].width, elements["Window_Rect"].height)), (elements["Window_Rect"].x,elements["Window_Rect"].y))
        scanTabColor = windowColor

    pygame.display.update()
