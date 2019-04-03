import data
import model
import numpy as np 
import logging
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import axes3d
import copy
import time

def dataVisualization(dataName):
    '''
    对数据做一些可视化处理，方便分析;
    '''
    #画出每个路口出发的车辆数目
    if dataName == 'carsFromEachCross':
        crossNum = len(data.crossList)
        carsFromEachCrossNum = np.zeros(crossNum)
        for i in range(crossNum):
            carsFromEachCrossNum[i] = len(data.carsFromEachCross[i])
        plt.plot(range(crossNum),carsFromEachCrossNum)
        plt.title('Cars\' Num From Each Cross')
        plt.show()
        plt.clf()
    #画出要到达每个路口的车辆数目
    if dataName == 'carsToEachCross':
        crossNum = len(data.crossList)
        carsToEachCrossNum = np.zeros(crossNum)
        for i in range(crossNum):
            carsToEachCrossNum[i] = len(data.carsToEachCross[i])
        plt.plot(range(crossNum),carsToEachCrossNum)
        plt.title('Cars\' Num To Each Cross')
        plt.show()
        plt.clf()
    #画出每条道路的长度
    if dataName == 'roadLength':
        roadNum = len(data.roadList)
        roadLength = np.zeros(roadNum)
        for i in range(roadNum):
            roadLength[i] = data.roadDict[data.roadList[i]].roadLen
        plt.plot(range(roadNum),roadLength)
        plt.title('Road Length')
        plt.show()
        plt.clf()
    #画出最短路径的情况
    if dataName == 'shortestPathLength':
        x,y = np.meshgrid(range(len(data.crossList)), range(len(data.crossList)))
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        #ax.set_zlim(0, 10000)
        ax.plot_wireframe(x, y, data.shortestPathLength, rstride=1,  cstride=1)
        plt.show()
        plt.clf()
    #画出地图，查看情况
    if dataName == 'crossMap':
        #循环一遍确定地图的范围，并提取出所有坐标点
        maxX = 0
        minX = 0
        maxY = 0
        minY = 0
        x = []
        y = []
        crossNoList = []
        for cross in data.crossDict.values():
            coordinate = cross.getCoordinate()
            x.append(coordinate[0])
            y.append(coordinate[1])
            crossNoList.append(cross.crossNo)
            if coordinate[0] > maxX:
                maxX = coordinate[0]
            elif coordinate[0] < minX:
                minX = coordinate[0]
            if coordinate[1] > maxY:
                maxY = coordinate[1]
            elif coordinate[1] < minY:
                minY = coordinate[1]
        plt.scatter(x,y)
        #画出所有的道路,并标记道路的编号
        for road in data.roadDict.values():
            coordinateFrom = data.crossDict[road.fromId].getCoordinate()
            coordinateTo = data.crossDict[road.toId].getCoordinate()
            xTemp = [coordinateFrom[0],coordinateTo[0]]
            yTemp = [coordinateFrom[1],coordinateTo[1]]
            plt.plot(xTemp,yTemp,color='darkgrey',linewidth=3+5*(1-(road.roadLen-data.minRoadLength)/(data.maxRoadLength-data.minRoadLength)))
            xCenter = (coordinateFrom[0]+coordinateTo[0])/2
            yCenter = (coordinateFrom[1]+coordinateTo[1])/2
            plt.text(xCenter-0.15,yCenter,'%d' % road.roadNo,fontsize=10,color='red')
        #画出所有在树中的道路
        for roadNo in data.roadInTheTree:
            coordinateFrom = data.crossDict[data.roadDict[roadNo].fromId].getCoordinate()
            coordinateTo = data.crossDict[data.roadDict[roadNo].toId].getCoordinate()
            xTemp = [coordinateFrom[0],coordinateTo[0]]
            yTemp = [coordinateFrom[1],coordinateTo[1]]
            plt.plot(xTemp,yTemp,color='dimgrey')
        #标记出所有路口的位置
        for i in range(len(crossNoList)):
            plt.text(x[i]-0.15,y[i],'%d' % crossNoList[i],fontsize=10,color='green')
        plt.show()
        plt.clf()
    #画出所有道路在路径中出现的次数
    elif dataName == 'roadInPath':
        roadNum = len(data.roadList)
        roadInPathNumDict = dict()
        for roadNo in data.roadList:
            roadInPathNumDict.update({roadNo:0})
        for car in data.carDict.values():
            for roadNo in data.shortestPathList[car.maxSpeed][car.fromId][car.toId]:
                roadInPathNumDict[roadNo] += 1
        roadInPathNumList = []
        for roadNo in data.roadList:
            roadInPathNumList.append(roadInPathNumDict[roadNo])
        plt.plot(data.roadList,roadInPathNumList)
        plt.show()
        plt.clf()
    else:
        return