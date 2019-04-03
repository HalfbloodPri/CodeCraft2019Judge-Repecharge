import numpy as np
import model
import data
import time
import logging

def readData(roadFilePath,carFilePath,crossFilePath,preAnswerFilePath):
    '''
    读出数据;
    '''
    timeBegin = time.time()
    #读取路口信息
    with open(crossFilePath,'r') as crossDataFile:
        crossData = crossDataFile.read().splitlines()
    length = len(crossData)
    newCrossNoDict = dict()      #文件中路口编号到新的路口编号的映射，新的路口编号从0开始依次递增；
    newCrossNo = 0      #新的路口编号
    for i in range(length):
        if crossData[i][0] == '#':
            continue
        crossInfo = tuple(eval(crossData[i]))
        newCrossNoDict.update({crossInfo[0]:newCrossNo})
        data.crossDict.update({newCrossNo:model.Cross(crossNo=newCrossNo,roadNorth=crossInfo[1],\
            roadEast=crossInfo[2],roadSouth=crossInfo[3],roadWest=crossInfo[4])})
        data.crossList.append(newCrossNo)
        data.newCrossNoToOrigiNo.update({newCrossNo:crossInfo[0]})
        newCrossNo += 1
    data.crossList.sort()

    #读出道路信息
    with open(roadFilePath,'r') as roadDataFile:
        roadData = roadDataFile.read().splitlines()
    length = len(roadData)
    for i in range(length):
        if roadData[i][0] == '#':
            continue
        roadInfo = tuple(eval(roadData[i]))
        data.roadDict.update({roadInfo[0]:model.Road(roadNo=roadInfo[0],roadLen=roadInfo[1],\
            maxSpeed=roadInfo[2],laneNum=roadInfo[3],fromId=newCrossNoDict[roadInfo[4]],\
            toId=newCrossNoDict[roadInfo[5]],isDuplex=roadInfo[6])})
        data.roadList.append(roadInfo[0])
        if roadInfo[2] > data.maxSpeed:
            data.maxSpeed = roadInfo[2]
        if roadInfo[2] < data.minSpeed:
            data.minSpeed = roadInfo[2]
        if roadInfo[1] > data.maxRoadLength:
            data.maxRoadLength = roadInfo[1]
        if roadInfo[1] < data.minRoadLength:
            data.minRoadLength = roadInfo[1]
    data.roadList.sort()

    #读出车辆信息
    with open(carFilePath,'r') as carDataFile:
        carData = carDataFile.read().splitlines()
    length = len(carData)
    for i in range(length):
        if carData[i][0] == '#':
            continue
        carInfo = tuple(eval(carData[i]))
        data.carDict.update({carInfo[0]:model.Car(carNo=carInfo[0],fromId=newCrossNoDict[carInfo[1]],\
            toId=newCrossNoDict[carInfo[2]],maxSpeed=carInfo[3],planTime=carInfo[4],isPriority=carInfo[5],\
            isPreset=carInfo[6])})
        data.carList.append(carInfo[0])
        if carInfo[3] not in data.speeds:
            data.speeds.append(carInfo[3])
        if carInfo[3] > data.maxSpeed:
            data.maxSpeed = carInfo[3]
        if carInfo[3] < data.minSpeed:
            data.minSpeed = carInfo[3]
    data.carList.sort()

    '''
    接下来进行data中其他数据的初始化；
    '''
    #在数据读入完成之后，可以先确定某条道路进入某个路口的方向，即正向还是反向，以备用；
    for cross in data.crossDict.values():
        cross.confirmRoadsDirection()
    #初始化从每个路口出发的车辆
    initCarsFromEachCross()
    #初始化到达每个路口的车辆
    initCarsToEachCross()
    #初始化路口之间的道路编号
    initRoadBetweenCrossed()
    #初始化路口地图
    #buildMap()

    logging.info('Initial data:%f' % (time.time()-timeBegin))

def initRoadBetweenCrossed():
    data.roadBetweenCrosses = model.TwoDDict()
    for road in data.roadDict.values():
        data.roadBetweenCrosses.update(road.fromId,road.toId,road.roadNo)
        if road.isDuplex:
            data.roadBetweenCrosses.update(road.toId,road.fromId,road.roadNo)

def initCarsToEachCross():
    '''
    初始化到达每个路口的车辆；
    '''
    crossNum = len(data.crossList)
    data.carsToEachCross = [[] for i in range(crossNum)]
    for car in data.carDict.values():
        data.carsToEachCross[car.toId].append(car.carNo)

def initCarsFromEachCross():
    '''
    初始化在每个路口等待出发的车辆，并排序；
    按照速度越快优先级越高，计划出发时间越早优先级越高，编号越小优先级越高的原则排序；
    且优先级 速度>计划出发时间>编号；
    优先级越高越靠近列表尾部；
    '''
    crossNum = len(data.crossList)
    data.carsFromEachCross = [[] for i in range(crossNum)]
    for car in data.carDict.values():
        i = 0
        while i<(len(data.carsFromEachCross[car.fromId])):
            if data.carDict[data.carsFromEachCross[car.fromId][i]].maxSpeed > car.maxSpeed:
                data.carsFromEachCross[car.fromId].insert(i,car.carNo)
                break
            elif data.carDict[data.carsFromEachCross[car.fromId][i]].maxSpeed == car.maxSpeed \
                and data.carDict[data.carsFromEachCross[car.fromId][i]].planTime < car.planTime:
                data.carsFromEachCross[car.fromId].insert(i,car.carNo)
                break
            elif data.carDict[data.carsFromEachCross[car.fromId][i]].maxSpeed == car.maxSpeed \
                and data.carDict[data.carsFromEachCross[car.fromId][i]].planTime == car.planTime\
                and data.carDict[data.carsFromEachCross[car.fromId][i]].carNo < car.carNo:
                data.carsFromEachCross[car.fromId].insert(i,car.carNo)
                break
            else:
                i += 1
        #如果没有在列表中发现优先级比它高的车辆，则直接加入到列表尾部
        if i == len(data.carsFromEachCross[car.fromId]):
            data.carsFromEachCross[car.fromId].append(car.carNo)

def buildMap():
    '''
    构建map的目的是寻找最靠近“中心”的的路口，作为树形图的根节点；
    这个map构建假设道路都是直线，即使道路是弯曲的，对我们的目的影响也不大；
    我们可以假设路口0的第一条道路是北方向，那么就可以把其他所有的道路的方向确定下来；
    '''
    #起始路口0坐标值设为（0,0），并以此路口为起点遍历得到所有路口的坐标值
    data.crossMap = model.TwoDDict()
    data.crossMap.update(0,0,0)
    data.crossDict[0].setCoordinate(0,0)

    #定义一个迭代函数，用于遍历
    crossToRun = []
    northRoadNoToBe = []
    def runOverCross():
        if crossToRun == []:
            return
        crossLocal = data.crossDict[crossToRun.pop()]
        northRoadNo = northRoadNoToBe.pop()
        #按顺序遍历北，东，南，西方向所连接的路口
        for directionNo in range(4):
            #根据路口所连接的各条道路遍历其他路口
            #roadNo即是某个方向上连接的道路的编号
            roadNo = crossLocal.roads[directionNo]
            if (roadNo == -1) or (roadNo not in data.roadDict):
                #-1代表该路口在该方向上没有道路,不在字典中说明道路未被记录，跳过
                continue
            else:
                road = data.roadDict[roadNo]
                #下面得到该道路另一端路口的编号
                if road.fromId == crossLocal.crossNo:
                    crossRemoteNo = road.toId
                else:
                    crossRemoteNo = road.fromId
                crossRemote = data.crossDict[crossRemoteNo]
                #如果该路口已经有坐标信息了，则不再需要进一步操作
                if crossRemote.hasCoordinate():
                    continue
                else:
                    #根据方向和路长计算出远端路口的坐标
                    #并且需要确定远端路口北方向道路的编号
                    roadInNo = crossRemote.roads.index(roadNo)#此道路在远端路口的道路列表中的编号
                    remoteNorthRoadNo = None #远方路口中北方道路的序号
                    coordinateLocal = crossLocal.getCoordinate()
                    #roadLen = road.roadLen
                    roadLen = 1
                    if directionNo == northRoadNo:        #北
                        xRemote = coordinateLocal[0]
                        yRemote = coordinateLocal[1]+roadLen
                        remoteNorthRoadNo = (roadInNo+2)%4
                    elif directionNo == (northRoadNo+1)%4:      #东
                        xRemote = coordinateLocal[0]+roadLen
                        yRemote = coordinateLocal[1]
                        remoteNorthRoadNo = (roadInNo+1)%4
                    elif directionNo == (northRoadNo+2)%4:      #南
                        xRemote = coordinateLocal[0]
                        yRemote = coordinateLocal[1]-roadLen
                        remoteNorthRoadNo = roadInNo
                    else:                       #西
                        xRemote = coordinateLocal[0]-roadLen
                        yRemote = coordinateLocal[1]
                        remoteNorthRoadNo = (roadInNo+3)%4
                    crossRemote.setCoordinate(xRemote,yRemote)
                    data.crossMap.update(xRemote,yRemote,crossRemoteNo)
                    crossToRun.insert(0,crossRemoteNo)
                    northRoadNoToBe.insert(0,remoteNorthRoadNo)
        runOverCross()

    crossToRun.append(0)
    northRoadNoToBe.append(0)
    runOverCross()