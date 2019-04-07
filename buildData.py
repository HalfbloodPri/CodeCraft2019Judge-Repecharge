import numpy as np
import model
import data
import time
import logging

def readData(roadFilePath,carFilePath,crossFilePath,preAnswerFilePath,answerFilePath):
    '''
    读出数据;
    '''
    timeBegin = time.time()
    #读取路口信息
    with open(crossFilePath,'r') as crossDataFile:
        crossData = crossDataFile.read().splitlines()
    length = len(crossData)
    #这里给路口重新编号是因为寻找最短路径时需要建立邻接表；如果只是做判题器的话，好像不需要重新编号；
    newCrossNo = 0      #新的路口编号
    for i in range(length):
        if crossData[i][0] == '#':
            continue
        crossInfo = tuple(eval(crossData[i]))
        data.origiCrossNoToNewNo.update({crossInfo[0]:newCrossNo})
        data.crossDict.update({crossInfo[0]:model.Cross(crossNo=crossInfo[0],roadNorth=crossInfo[1],\
            roadEast=crossInfo[2],roadSouth=crossInfo[3],roadWest=crossInfo[4])})
        data.crossList.append(crossInfo[0])
        newCrossNo += 1
    #在行车时，需要按编号从小到大遍历路口，因此还需要原编号的排序表
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
            maxSpeed=roadInfo[2],laneNum=roadInfo[3],fromId=roadInfo[4],\
            toId=roadInfo[5],isDuplex=roadInfo[6])})
        data.roadList.append(roadInfo[0])
    data.roadList.sort()

    #读出车辆信息
    carsDict = dict()   #用于读入answer时判断车辆是否在图中，以及是否所有车辆已读入完毕
    with open(carFilePath,'r') as carDataFile:
        carData = carDataFile.read().splitlines()
    length = len(carData)
    for i in range(length):
        if carData[i][0] == '#':
            continue
        carInfo = tuple(eval(carData[i]))
        data.carDict.update({carInfo[0]:model.Car(carNo=carInfo[0],fromId=carInfo[1],\
            toId=carInfo[2],maxSpeed=carInfo[3],planTime=carInfo[4],isPriority=carInfo[5],\
            isPreset=carInfo[6])})
        data.carList.append(carInfo[0])
        carsDict.update({carInfo[0]:True})
    data.carList.sort()

    #读入路径信息，即preAnswer和answer
    '''
    #先读preAnswer,不需要做合法性判断
    with open(preAnswerFilePath,'r') as preAnswerFile:
        preAnswerData = preAnswerFile.read().splitlines()
    length = len(preAnswerData)
    for i in range(length):
        if preAnswerData[i][0] == '#':
            continue
        pathInfo = tuple(eval(preAnswerData[i]))
        car = data.carDict[pathInfo[0]]
        car.setSetOffTime(pathInfo[1])
        for j in range(2,len(pathInfo)):
            car.addToPath(pathInfo[j])
        carsDict.pop(pathInfo[0])
    '''
    #读入answer
    with open(answerFilePath,'r') as answerFile:
        answerData = answerFile.read().splitlines()
    length = len(answerData)
    for i in range(length):
        if answerData[i][0] == '#':
            continue
        pathInfo = tuple(eval(answerData[i]))
        #判断路径是否包含了必要的信息，即长度是否大于等于3
        if len(pathInfo) < 3:
            logging.info('Car:%d, illegal path!' % (pathInfo[0]))
            exit(1)
        #如果车辆已经在preAnswer中，或根本不存在，退出
        if pathInfo[0] not in carsDict:
            logging.info('Car:%d does not exist in the map or already exists in pre_answer!' % (pathInfo[0]))
            exit(1)
        car = data.carDict[pathInfo[0]]
        #如果车辆的实际出发时间小于计划出发时间，退出
        if car.planTime > pathInfo[1]:
            logging.info('Car:%d, set off time:%d, plan time:%d, illegal!' % (pathInfo[0],pathInfo[1],car.planTime))
            exit(1)
        car.setSetOffTime(pathInfo[1])
        #判断路径起点是否合法
        if pathInfo[2] not in data.roadDict:
            logging.info('Car:%d, road:%d does not exist in the map!' % (pathInfo[0],pathInfo[2]))
            exit(1)
        road = data.roadDict[pathInfo[2]]
        if road.fromId == car.fromId:
            lastCross = road.toId
        elif road.toId == car.fromId and road.isDuplex:
            lastCross = road.fromId
        else:
            logging.info('Car:%d, road:%d, illegal begin road!' % (pathInfo[0],pathInfo[2]))
            exit(1)
        car.addToPath(pathInfo[2])
        #判断路径中的道路是否连续
        for j in range(3,len(pathInfo)):
            if pathInfo[j] not in data.roadDict:
                logging.info('Car:%d, road:%d does not exist in the map!' % (pathInfo[0],pathInfo[j]))
                exit(1)
            road = data.roadDict[pathInfo[j]]
            if road.fromId == lastCross:
                lastCross = road.toId
            elif road.toId == lastCross and road.isDuplex:
                lastCross = road.fromId
            else:
                logging.info('Car:%d, road:%d, lastCross:%d, discrete road!' % (pathInfo[0],pathInfo[j], lastCross))
                exit(1)
            car.addToPath(pathInfo[j])
        #判断路径终点是否合法
        if lastCross != car.toId:
            logging.info('Car:%d, road:%d, illegal end road!' % (pathInfo[0],pathInfo[-1]))
            exit(1)
        carsDict.pop(pathInfo[0])
    if bool(carsDict):
        logging.info('There are cars not in the answer!')
        for car in carsDict.values():
            logging.info(car.carNo)
        exit(1)

    '''
    接下来进行data中其他数据的初始化；
    '''
    #在数据读入完成之后，可以先确定某条道路进入某个路口的方向，即正向还是反向，以备用；
    for cross in data.crossDict.values():
        cross.confirmRoadsDirection()
    #初始化从每个路口出发的车辆
    initCarsFromEachCross()

    logging.info('Initial data:%f' % (time.time()-timeBegin))

def initCarsFromEachCross():
    '''
    初始化在每个道路上等待出发的车辆，并排序；
    每个道路的待出发车辆都分成优先车辆和非优先车辆两个队列；
    当两队列内最高优先级的车辆都可以出发时，优先车辆的优先级高于非优先车辆；
    每个队列内的优先级按照实际出发时间越早优先级越高，编号越小优先级越高的原则排序；
    优先级越高越靠近列表尾部；
    '''
    for car in data.carDict.values():
        road = data.roadDict[car.path[0]]
        cross = data.crossDict[car.fromId]
        roadDirection = cross.roadsDirections[road.roadNo]  #0代表是正向驶入此路，1代表反向驶入此路
        roadDirection = 1-roadDirection        #改为1代表是正向驶入此路，0代表反向驶入此路
        if car.isPriority:
            sequeue = road.carInInitList[roadDirection][0]       #优先车辆的队列
        else:
            sequeue = road.carInInitList[roadDirection][1]       #非优先车辆的队列
        i = 0
        while i<(len(sequeue)):
            if data.carDict[sequeue[i]].setOffTime < car.setOffTime:
                sequeue.insert(i,car.carNo)
                break
            elif data.carDict[sequeue[i]].setOffTime == car.setOffTime \
                and sequeue[i] < car.carNo:
                sequeue.insert(i,car.carNo)
                break
            else:
                i += 1
        #如果没有在列表中发现优先级比它高的车辆，则直接加入到列表尾部
        if i == len(sequeue):
            sequeue.append(car.carNo)