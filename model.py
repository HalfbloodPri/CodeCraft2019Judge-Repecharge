#存放所需要的车辆、道路、路口等数据结构；
import numpy as np
import data
import logging

class Road():

    def __init__(self,roadNo=None,roadLen=None,maxSpeed=None,laneNum=None,fromId=None,toId=None,isDuplex=None):
        self.roadNo = roadNo      #道路编号
        self.roadLen = roadLen    #道路长度
        self.maxSpeed = maxSpeed  #道路限速
        self.laneNum = laneNum    #道路单向的车道数
        self.fromId = fromId      #道路的起始路口编号
        self.toId = toId          #道路的终止路口编号
        self.isDuplex = isDuplex  #标记是否为双向道路，1代表是双向道路，0代表不是
        self.initLanes()
        self.weight = self.roadLen/(self.maxSpeed*self.laneNum)
        #在本路口等待出发的车辆，[1]是正方向队列，[0]是反方向队列，[*][0]是优先车辆，[*][1]是非优先车辆
        self.carInInitList = [[[],[]],[[],[]]]

    def initLanes(self):
        '''
        初始化此道路上各个车道的车辆情况;
        每个车道都用一个列表表示当前时刻车道上的车的队列;
        先进入的车辆在列表的尾部，后进入的车辆在列表首部;
        如果是双向车道，[1]表示正向车道情况，[0]表示反向车道情况；
        '''
        self.lanes = [[[] for i in range(self.laneNum)] for j in range(2)]
        #该道路两个方向上的等待车辆的优先级队列
        self.carSequeue = [[] for j in range(2)]

    def carIn(self,carNo,laneNo,direction):
        '''
        车辆驶入道路;
        carNo:进入的车辆的编号;laneNo:进入的车道编号;
        direction:1代表驶入正向车道，0代表驶入反向车道；
        '''
        self.lanes[direction][laneNo].insert(0,carNo)

    def carOut(self,laneNo,direction):
        '''
        车辆驶出道路;
        laneNo:驶出车辆所在车道的编号；
        direction:1代表驶出正向车道，0代表驶出反向车道；
        '''
        self.lanes[direction][laneNo].pop()

    def updateAllCars(self,timeNow):
        '''
        遍历该道路上的所有车辆，对于不必进入waiting状态的车辆更新车辆的状态;
        '''
        if self.isDuplex:
            directions = [0,1]
        else:
            directions = [1]
        for laneNo in range(self.laneNum):
            for direction in directions:
                carNum = len(self.lanes[direction][laneNo])     #该车道上的车辆数目
                roadEnd = self.roadLen      #车辆能行驶到的最大位置，可能是道路的尽头，也可能是前一辆车的位置
                statusAhead = 1     #该车辆前方车辆的状态，1代表waitting
                for i in range(carNum-1,-1,-1):
                    #行驶速度为道路限速和车辆自身最大速度的较小者
                    car = data.carDict[self.lanes[direction][laneNo][i]]
                    speed = min(self.maxSpeed,car.maxSpeed)
                    #假定按此速度行驶，可到达的位置为newPosition
                    newPosition = car.position + speed
                    #如果车辆驶出能行驶的最大位置，则进入等待状态，由路口进行调度
                    if newPosition >= roadEnd:
                        if statusAhead == 1:
                            car.startWaiting()
                            roadEnd = car.position
                        else:
                            car.setPosition(newPosition-1)
                            roadEnd = newPosition-1
                            car.endWaiting()
                            statusAhead = 0
                    else:
                        car.setPosition(newPosition)
                        roadEnd = newPosition
                        car.endWaiting()
                        statusAhead = 0
        #优先车辆上路
        self.runCarInInitList(timeNow,True)
    
    def updateCars(self,timeNow,direction,laneNo):
        '''
        遍历某方向某车道上的车；
        '''
        lane = self.lanes[direction][laneNo]
        carNum = len(lane)     #该车道上的车辆数目
        roadEnd = self.roadLen      #车辆能行驶到的最大位置，可能是道路的尽头，也可能是前一辆车的位置
        statusAhead = 1     #该车辆前方车辆的状态，1代表waitting
        for i in range(carNum-1,-1,-1):
            #行驶速度为道路限速和车辆自身最大速度的较小者
            car = data.carDict[lane[i]]
            #如果该车辆仍未进入终止状态
            if not car.finish:
                speed = min(self.maxSpeed,car.maxSpeed)
                #假定按此速度行驶，可到达的位置为newPosition
                newPosition = car.position + speed
                #如果车辆驶出能行驶的最大位置，则继续等待
                if newPosition >= roadEnd:
                    if statusAhead == 1:
                        car.startWaiting()
                        roadEnd = car.position
                    else:
                        car.setPosition(newPosition-1)
                        roadEnd = newPosition-1
                        car.endWaiting()
                        statusAhead = 0
                else:
                    car.setPosition(newPosition)
                    roadEnd = newPosition
                    car.endWaiting()
                    statusAhead = 0
            else:
                break
        #优先车辆上路
        self.runCarInInitList(timeNow,True,dire=direction)

    def runCarInInitList(self,timeNow,priority,dire=2):
        #priority为True，只允许优先车辆上路;direction表示上路车辆进入道路的方向，1表示正向,0表示反向,2表示两个方向都变遍历；
        if dire == 1:
            directions = [1]
        elif dire == 0:
            directions = [0]
        else:
            directions = [0,1]
        for direction in directions:
            #先计算该道路在该方向上各车道是否还有位置进入，求出能进入的车道数和能行驶的最大距离
            freeDistance = np.zeros(self.laneNum)
            statusAhead = []        #对应车道最后一辆车的状态
            for i in range(self.laneNum):
                car = data.carDict[self.lanes[direction][i][0]]
                freeDistance[i] = car.position-1
                statusAhead.append(car.finish)
            laneNo = 0
            endCondition = 1    #优先车辆无法进入道路的终止条件：1代表是因为未到达出发时间而无法进入道路，那么非优先车辆仍有机会进入道路；
            #0代表因为道路没有空位或前方有等待车辆阻挡而无法进入道路，那么非优先车辆因优先级较低，不能进入道路；
            while laneNo < self.laneNum:
                if freeDistance[laneNo] == 0:
                    laneNo += 1
                    continue
                car = data.carDict[self.carInInitList[direction][0][-1]]       #取优先级最高的一辆优先车辆
                if car.setOffTime > timeNow:
                    break
                speed = min(car.maxSpeed,self.maxSpeed)
                if speed <= freeDistance[laneNo]:   #如果未被阻挡，直接进入道路
                    freeDistance[laneNo] = speed-1
                    self.carIn(car.carNo,laneNo,True)
                    car.moveToNextRoad(speed,laneNo)
                    self.carInInitList[direction][0].pop()
                elif statusAhead[laneNo]:   #如果被阻挡，但前车是终止状态
                    self.carIn(car.carNo,laneNo,True)
                    car.moveToNextRoad(freeDistance[laneNo],laneNo)
                    freeDistance[laneNo] = freeDistance[laneNo]-1
                    self.carInInitList[direction][0].pop()
                else:                       #被阻挡，且前车为等待状态，不得上路
                    endCondition = 0
                    break
            if not priority:
                if endCondition == 1 or laneNo < self.laneNum:
                    while laneNo < self.laneNum:
                        if freeDistance[laneNo] == 0:
                            laneNo += 1
                            continue
                        car = data.carDict[self.carInInitList[direction][1][-1]]       #取优先级最高的一辆非优先车辆
                        if car.setOffTime > timeNow:
                            break
                        speed = min(car.maxSpeed,self.maxSpeed)
                        if speed <= freeDistance[laneNo]:   #如果未被阻挡，直接进入道路
                            freeDistance[laneNo] = speed-1
                            self.carIn(car.carNo,laneNo,True)
                            car.moveToNextRoad(speed,laneNo)
                            self.carInInitList[direction][1].pop()
                        elif statusAhead[laneNo]:   #如果被阻挡，但前车是终止状态
                            self.carIn(car.carNo,laneNo,True)
                            car.moveToNextRoad(freeDistance[laneNo],laneNo)
                            freeDistance[laneNo] = freeDistance[laneNo]-1
                            self.carInInitList[direction][1].pop()
                        else:                       #被阻挡，且前车为等待状态，不得上路
                            break
    
    def createCarSequeue(self,dire):
        '''
        构建等待车辆的优先级队列；
        '''
        if dire == 1:
            directions = [1]
        elif dire == 0:
            directions = [0]
        else:
            directions = [0,1]
        for direction in directions:
            pass

class Cross():

    def __init__(self,crossNo=None,roadNorth=None,roadEast=None,roadSouth=None,roadWest=None):
        self.crossNo = crossNo          #路口编号
        #按顺序存储路口所连接的道路的编号
        self.roads=[roadNorth,roadEast,roadSouth,roadWest]
        self.confirmDorLorR()
        self.coordinate = None

    def confirmRoadsDirection(self):
        '''
        确定每条道路进入该路口的方向是正向(forward)还是反向(backward)的;
        '''
        self.roadsDirections=dict()     #1代表正向，0代表反向
        for roadNo in self.roads:
            if roadNo != -1:
                if data.roadDict[roadNo].toId == self.crossNo:
                    self.roadsDirections.update({roadNo:1})
                else:
                    self.roadsDirections.update({roadNo:0})

    def confirmDorLorR(self):
        '''
        四条道路是按照顺时针方向传入的，可以确定从某条道路到另一条道路是要直行(D)，左转(L)，还是右转(R);
        用数字1代表直行，2代表左转，3代表右转；
        '''
        turnDirections = [3,1,2]
        self.DLR = TwoDDict()
        for i in range(4):
            if self.roads[i] == -1:
                continue
            for j in range(1,4):
                if self.roads[i-j] == -1:
                    continue
                else:
                    self.DLR.update(self.roads[i],self.roads[i-j],turnDirections[j-1])

    def sortWaitingCarsOnEachRoad(self):
        '''
        在每次开始调度路口的车辆时，给每个路口的等待的车辆进行优先级排序，
        这时暂不考虑转向问题，仅以车道数和车辆位置进行排序；
        '''
        #首先得到每条道路上在等待车辆的列表，并且车道数目小的在列表尾部，代表优先级高
        self.waitingCarsList = [[] for i in range(4)]
        for i in range(4):
            roadNo = self.roads[i]
            if roadNo == -1:
                continue
            carList = (data.roadDict[roadNo].forwardLanes if self.roadsDirections[i] == 1 else \
                        data.roadDict[roadNo].backwardLanes).copy()
            for j in range(data.roadDict[roadNo].laneNum):
                for k in range(len(carList[j])):
                    if data.carDict[carList[j][k]].waiting:
                        self.waitingCarsList[i].insert(0,carList[j][k])
                    else:
                        break
        #然后对等待车辆的列表按照位置进行排序，确定最终优先级，越靠近列表尾不优先级越高
        for i in range(4):
            #冒泡排序
            for j in range(len(self.waitingCarsList[i]),1,-1):
                for k in range(j-1):
                    if data.carDict[self.waitingCarsList[i][k]].position > \
                        data.carDict[self.waitingCarsList[i][k+1]].position:
                        tempCarNo = self.waitingCarsList[i][k]
                        self.waitingCarsList[i][k] = self.waitingCarsList[i][k+1]
                        self.waitingCarsList[i][k+1] = tempCarNo

    def updateCars(self):
        pass

class Car():

    def __init__(self,carNo=None,fromId=None,toId=None,maxSpeed=None,planTime=None,isPriority=0,isPreset=0):
        self.carNo = carNo          #车辆编号
        self.fromId = fromId        #出发地路口编号
        self.toId = toId            #目的地路口编号
        self.maxSpeed = maxSpeed    #车辆自身最大速度
        self.planTime = planTime    #车辆计划出发时间
        self.waiting = False        #该车辆是否处于等待状态，True代表处于等待状态
        self.finish = False         #True代表该车进入终止状态
        self.position = -1          #该车辆在车道上的位置
        self.laneNo = -1
        self.roadNo = -1
        self.setOffTime = self.planTime     #该车辆的出发时间
        self.isPriority = isPriority
        self.isPreset = isPreset
        self.path = []      #这辆车的路径
        self.nextRoad = 0   #该车辆要进入的下一个道路在path中的编号

    def setPosition(self,position,laneNo=None):
        '''
        设定当前车辆的位置;
        '''
        self.position = position
        if laneNo != None:
            self.laneNo = laneNo

    def startWaiting(self):
        '''
        让车辆进入等待状态;
        '''
        self.waiting = True
        self.finish = False

    def endWaiting(self):
        '''
        结束等待状态;
        '''
        self.waiting = False
        self.finish = True

    def setSetOffTime(self,time):
        self.setOffTime = time

    def addToPath(self,roadNo):
        self.path.append(roadNo)

    def moveToNextRoad(self,position,laneNo):
        self.position = position
        self.laneNo = laneNo
        self.roadNo = self.path[self.nextRoad]
        self.nextRoad += 1

    def getNextRoad(self):
        if self.nextRoad < len(self.path):
            return self.path[self.nextRoad]
        else:
            return -1   #-1表示该车前方就是目的路口，不再需要进入下一道路

#二维字典
class TwoDDict():

    def __init__(self):
        self.dict = dict()

    def value(self,x,y):
        '''
        返回存储的值;
        '''
        if self.isIn(x,y):
            return self.dict[x][y]
        else:
            return None

    #添加或更新一个值
    def update(self,x,y,value):
        if x in self.dict:
            self.dict[x].update({y: value})
        else:
            self.dict.update({x:{y: value}})

    #删除一个值
    def delete(self,x,y):
        if x in self.dict:
            if y in self.dict[x]:
                self.dict[x].pop(y)
                if self.dict[x] == {}:
                    self.dict.pop(x)

    #判断一个key值是否在字典内
    def isIn(self,x,y):
        if x in self.dict:
            if y in self.dict[x]:
                return True
            else:
                return False
        else:
            return False

    #打印出所有节点的信息
    def print(self):
        for keyX in self.dict:
            for keyY in self.dict[keyX]:
                logging.info(keyX,keyY,self.dict[keyX][keyY])