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

    def initLanes(self):
        '''
        初始化此道路上各个车道的车辆情况;
        每个车道都用一个列表表示当前时刻车道上的车的队列;
        先进入的车辆在列表的尾部，后进入的车辆在列表首部;
        如果是双向车道，forwardLanes表示正向车道情况，backwardLanes表示反向车道情况；
        '''
        self.forwardLanes = [[] for i in range(self.laneNum)]
        if self.isDuplex:
            self.backwardLanes = [[] for i in range(self.laneNum)]

    def carIn(self,carNo,laneNo,isForward):
        '''
        车辆驶入道路;
        carNo:进入的车辆的编号;laneNo:进入的车道编号;
        isForward:True代表驶入正向车道，False代表驶入反向车道；
        '''
        if isForward:
            self.forwardLanes[laneNo].insert(0,carNo)
        else:
            self.backwardLanes[laneNo].insert(0,carNo)

    def carOut(self,laneNo,isForward):
        '''
        车辆驶出道路;
        laneNo:驶出车辆所在车道的编号；
        isForward:True代表驶出正向车道，False代表驶出反向车道；
        '''
        if isForward:
            self.forwardLanes[laneNo].pop()
        else:
            self.backwardLanes[laneNo].pop()

    def updateCars(self,timeNow):
        '''
        遍历该道路上的所有车辆，对于不必进入waiting状态的车辆更新车辆的状态;
        '''
        for laneNo in range(self.laneNum):
            #首先遍历正向车道上的车辆；
            carNum = len(self.forwardLanes[laneNo])     #该车道上的车辆数目
            roadEnd = self.roadLen      #车辆能行驶到的最大位置，可能是道路的尽头，也可能是前一辆车的位置
            for i in range(carNum-1,-1,-1):
                #行驶速度为道路限速和车辆自身最大速度的较小者
                car = data.carDict[self.forwardLanes[laneNo][i]]
                #如果该车辆仍未更新
                if car.time < timeNow:
                    speed = min(self.maxSpeed,car.maxSpeed)
                    #假定按此速度行驶，可到达的位置为newPosition
                    newPosition = car.position + speed
                    #如果车辆驶出能行驶的最大位置，则进入等待状态，由路口进行调度
                    if newPosition >= roadEnd:
                        car.startWaiting()
                        roadEnd = car.position
                    else:
                        car.setPosition(newPosition)
                        roadEnd = newPosition
                        car.setTime(timeNow)
            if self.isDuplex:
                #然后遍历反向车道上的车辆；
                carNum = len(self.backwardLanes[laneNo])     #该车道上的车辆数目
                roadEnd = self.roadLen      #车辆能行驶到的最大位置，可能是道路的尽头，也可能是前一辆车的位置
                for i in range(carNum-1,-1,-1):
                    #行驶速度为道路限速和车辆自身最大速度的较小者
                    car = data.carDict[self.backwardLanes[laneNo][i]]
                    #如果该车辆仍未更新
                    if car.time < timeNow:
                        speed = min(self.maxSpeed,car.maxSpeed)
                        #假定按此速度行驶，可到达的位置为newPosition
                        newPosition = car.position + speed
                        #如果车辆驶出能行驶的最大位置，则进入等待状态，由路口进行调度
                        if newPosition >= roadEnd:
                            car.startWaiting()
                            roadEnd = car.position
                        else:
                            car.setPosition(newPosition)
                            roadEnd = newPosition
                            car.setTime(timeNow)

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
        self.roadsDirections=[]     #1代表正向，0代表反向，-1无意义
        for roadNo in self.roads:
            if roadNo == -1:
                self.roadsDirections.append(-1)
            elif data.roadDict[roadNo].toId == self.crossNo:
                self.roadsDirections.append(1)
            else:
                self.roadsDirections.append(0)

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

    #设定该路口的绝对坐标值
    def setCoordinate(self,x,y):
        self.coordinate = (x,y)

    def getCoordinate(self):
        return self.coordinate

    #判断该路口是否已经有坐标信息
    def hasCoordinate(self):
        if self.coordinate == None:
            return False
        else:
            return True

class Car():

    def __init__(self,carNo=None,fromId=None,toId=None,maxSpeed=None,planTime=None,isPriority=None,isPreset=None):
        self.carNo = carNo          #车辆编号
        self.fromId = fromId        #出发地路口编号
        self.toId = toId            #目的地路口编号
        self.maxSpeed = maxSpeed    #车辆自身最大速度
        self.planTime = planTime    #车辆计划出发时间
        self.runing = False         #该车辆是否已经出发，True代表已经出发
        self.done = False           #该车辆是否已经到达，True代表已经到达
        self.waiting = False        #该车辆是否处于等待状态，True代表处于等待状态
        self.time = 0               #该车辆目前所处的时刻，如果与系统时间相同，则表示该车辆的状态已经更新过了
        self.position = -1          #该车辆在车道上的位置
        self.setOffTime = self.planTime     #该车辆的出发时间
        self.isPriority = isPriority
        self.isPreset = isPreset

    def setPosition(self,position):
        '''
        设定当前车辆的位置;
        '''
        self.position = position

    def startWaiting(self):
        '''
        让车辆进入等待状态;
        '''
        self.waiting = True

    def endWaiting(self):
        '''
        结束等待状态;
        '''
        self.waiting = False

    def setTime(self,time):
        self.time = time

    def setSetOffTime(self,time):
        self.setOffTime = time

class Graph():
    
    def __init__(self):
        self.nodes = dict()     #存储节点的词典
        self.edges = dict()     #存储边的词典

    def addNode(self,nodeId,edges):
        self.nodes.update({nodeId:Node(edges)})

    def addEdge(self,edgeId,fromId,toId,weight,isDuplex):
        self.edges.update({edgeId:Edge(fromId,toId,weight,isDuplex)})

    def updateWeight(self,edgeId,newWeight):
        self.edges[edgeId].updateWeight(newWeight)

class Node():
    
    def __init__(self,value):
        self.value = value
        self.nextNodes = []

class Edge():
    
    def __init__(self,fromId,toId,weight,isDuplex):
        self.fromId = fromId    #该边的起点
        self.toId = toId        #该边的终点
        self.weight = weight    #该边对应的权值
        self.isDuplex = isDuplex    #是否为双向，1代表双向，0代表单项

    def updateWeight(self,newWeight):
        self.weight = newWeight

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

    #添加值为列表
    def addAsList(self,x,y):
        if x in self.dict:
            self.dict[x].update({y: []})
        else:
            self.dict.update({x:{y: []}})
    
    #更新列表中的值
    def updateAsList(self,x,y,value):
        if self.isIn(x,y):
            self.dict[x][y].append(value)

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

#三维字典
class ThreeDDict():

    def __init__(self):
        self.dict = dict()

    def value(self,x,y,z):
        '''
        返回存储的值;
        '''
        if self.isIn(x,y,z):
            return self.dict[x][y][z]
        else:
            return None

    #添加或更新一个值
    def update(self,x,y,z,value):
        if x in self.dict:
            if y in self.dict[x]:
                self.dict[x][y].update({z:value})
            else:
                self.dict[x].update({y:{z:value}})
        else:
            self.dict.update({x:{y:{z:value}}})

    #删除一个值
    def delete(self,x,y,z):
        if x in self.dict:
            if y in self.dict[x]:
                if z in self.dict[x][y]:
                    self.dict[x][y].pop(z)
                if self.dict[x][y] == {}:
                    self.dict[x].pop(y)
                if self.dict[x] == {}:
                    self.dict.pop(x)

    #判断一个key值是否在字典内
    def isIn(self,x,y,z):
        if x in self.dict:
            if y in self.dict[x]:
                if z in self.dict[x][y]:
                    return True
        return False