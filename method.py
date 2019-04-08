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
    crossesDoneNum = 0
    for i in range(len(data.crossList)):
        crossesDoneNum += data.crossDict[data.crossList[i]].updateRoads(timeNow)
    return crossesDoneNum

def creatAllCarSequeue():
    for i in range(len(data.roadList)):
        data.roadDict[data.roadList[i]].createCarSequeue()

def driveCarInInitList(timeNow):
    for i in range(len(data.roadList)):
        data.roadDict[data.roadList[i]].runCarInInitList(timeNow,False)

def runTheMap(timeNow):
    runOverRoads(timeNow)
    creatAllCarSequeue()
    while True:
        if runOverCross(timeNow) == len(data.crossList):
            break
    driveCarInInitList(timeNow)