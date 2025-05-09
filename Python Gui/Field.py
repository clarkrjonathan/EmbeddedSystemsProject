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
from Gui import *


#if its the initial scan it will just initialize to the objects
def updateScale(objs, scale, initialScale = True):
    xMin = min([x[0] for x in objs])
    yMin = min([x[1] for x in objs])

    xMax = max([x[0] for x in objs])
    yMax = max([x[1] for x in objs])

    scale["xMin"]  = xMin if (xMin < scale["xMin"]) or initialScale else scale["xMin"]
    scale["xMax"] = xMax if (xMax > scale["xMax"]) or initialScale else scale["xMax"]

    scale["yMin"] =  yMin if (yMin < scale["yMin"]) or initialScale else scale["yMin"]
    scale["yMax"] = yMax if (yMax > scale["yMax"]) or initialScale else scale["yMax"]

#object should be a list or tuple with elements x, y, radius
def scaleObject(obj, xScale, yScale, xMin, yMin, xSpan, ySpan, windowWidth, windowHeight):
    if(xScale > yScale):

        #locate origin
        obj[0] -= xMin

        obj[1] -= yMin

        #scale all
        obj[0] /= xScale    
        obj[1]  /= xScale
        obj[2] /= xScale

        #center our y
        obj[1] += (windowHeight/2) - ((ySpan/xScale)/2)


    else:
        #locate origin
        obj[0] -= xMin

        obj[1] -= yMin
        
        #scale all
        obj[0] /= yScale
        obj[1] /= yScale
        obj[2] /= yScale

        #center our x
        obj[0] += (windowWidth/2) - ((xSpan/yScale)/2)

#normalizes objects to be within a certain span at a specified offset
def normalizeObjects(objs, windowSurface, scale):
    windowWidth = windowSurface.get_width()
    windowHeight = windowSurface.get_height()

    #measure y span
    #measure x span

    #scale objects size by this too
    if(objs == -1):
        return -1
    
    #copy array
    normalized = [[k for k in x] for x in objs]


    xMin = scale["xMin"]
    yMin = scale["yMin"]

    xSpan = scale["xMax"] - scale["xMin"]
    xScale = xSpan/windowWidth
    
    ySpan = scale["yMax"] - scale["yMin"]
    yScale = ySpan/windowHeight

    

    for obj in normalized:
        scaleObject(obj, xScale, yScale, xMin, yMin, xSpan, ySpan, windowWidth, windowHeight)



    return normalized

#draw cybot
#cybotSprite is a list of x, y, angle, radius
def drawCybot(window, cybotSprite, color = (255, 0, 0)):
    #we have angle to draw
    if(len(cybotSprite) > 3):
        pygame.draw.circle(window, color, (cybotSprite[0], cybotSprite[1]), cybotSprite[3])

        #make size of mine which is 50mm
        frontDotSize = cybotSprite[3] * (50/185)

        xOffset = math.cos((cybotSprite[2]) * (math.pi/180)) * (cybotSprite[3] - frontDotSize)
        yOffset = math.sin((cybotSprite[2]) * (math.pi/180)) * (cybotSprite[3] - frontDotSize)

        pygame.draw.circle(window, (0,0,0), (cybotSprite[0] + xOffset, cybotSprite[1] + yOffset), frontDotSize)
    else:
        print("Cannot Draw cybot")

#redraws field surface when the data changes which is anytime we receive a new cybot position or fieldData
def updateField(surface, fieldScansIR, fieldScansPing, cybot, scale, otherObjects, cybotRadius = 185, pointRadius = 20):
    windowWidth = surface.get_width()
    windowHeight = surface.get_height()

    
    
    surface.fill((0,0,0,0))

    if(len(fieldScansPing) > 0):
        normalizedScan = normalizeObjects(fieldScansPing[-1], surface, scale)
        drawObjects(normalizedScan, surface, (0, 20, 255, 60))



    alphaMult = 50
    for i in range(len(fieldScansIR)):
        scan = fieldScansIR[i]
        normalizedScan = normalizeObjects(scan, surface, scale)
        alphaVal = (255 - ((len(fieldScansIR) - i) * alphaMult))
        alphaVal = 30 if alphaVal < 30 else alphaVal

        drawObjects(normalizedScan, surface, (255, 255, 255, alphaVal))

    

    scaledcybot = [x for x in cybot]
    scaledcybot.append(cybotRadius)

    scaledcybot[0] -= scale["xMin"]
    scaledcybot[1] -= scale["yMin"]

    xSpan = scale["xMax"] - scale["xMin"]
    xScale = (xSpan)/windowWidth
    
    ySpan = scale["yMax"] - scale["yMin"]
    yScale = (ySpan)/windowHeight


    if((xScale > yScale) and (xScale != 0)):
        scaledcybot[0] /= xScale
        scaledcybot[1] /= xScale
        scaledcybot[3] /= xScale

        scaledcybot[1] += (windowHeight/2) - ((ySpan/xScale)/2)

    elif ((yScale != 0)):
        scaledcybot[0] /= yScale
        scaledcybot[1] /= yScale
        scaledcybot[3] /= yScale

        scaledcybot[0] += (windowWidth/2) - ((xSpan/yScale)/2)

    for k in otherObjects:
        #scaleObject(obj, xScale, yScale, xMin, yMin, xSpan, ySpan, windowWidth, windowHeight):
        scaledK = k.copy()
        
        scaleObject(scaledK, xScale, yScale, scale["xMin"], scale["yMin"], xSpan, ySpan, windowWidth, windowHeight)

        pygame.draw.circle(surface, k[3], (scaledK[0], scaledK[1]), scaledK[2])

    drawCybot(surface, scaledcybot)
