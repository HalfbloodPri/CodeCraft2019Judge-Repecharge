import data
import model
import numpy as np 
import logging
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import axes3d
import copy
import time

def runOverRoads(timeNow):
    for i in range(len(data.roadList)):
        data.roadDict[data.roadList[i]].updateAllCars(timeNow)

def runOverCross(timeNow):
    for i in range(len(data.crossList)):
        data.crossDict[data.crossList[i]].updateRoads(timeNow)

def driveCarInInitList(timeNow):
    for i in range(len(data.roadList)):
        data.roadDict[data.roadList[i]].runCarInInitList(timeNow,False)

def runTheMap(timeNow):
    runOverRoads(timeNow)
    runOverCross(timeNow)
    driveCarInInitList(timeNow)