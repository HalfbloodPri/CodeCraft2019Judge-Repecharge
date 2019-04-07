#存放所需要的车辆、道路、路口等数据结构；
import numpy as np
import data
import logging
import time

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
                roadEnd = self.roadLen + 1     #车辆能行驶到的最大位置，可能是道路的尽头，也可能是前一辆车的位置
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
                            #如果是因为前方有等待车辆而进入等待状态，则加入到等待链中
                            if i < (carNum-1):
                                car.setWaitingFather(self.lanes[direction][laneNo][i+1])
                        else:
                            car.setPosition(roadEnd-1)
                            roadEnd = roadEnd-1
                            car.endWaiting()
                            statusAhead = 0
                    else:
                        car.setPosition(newPosition)
                        roadEnd = newPosition
                        car.endWaiting()
                        statusAhead = 0
        #优先车辆上路
        self.runCarInInitList(timeNow,True)
    
    def updateCars(self,timeNow,direction,laneNo,skipCars=0):
        '''
        遍历某方向某车道上的车；因为此函数是在路口循环内调用的，因此直行即可到达终点的车辆直接终止移除；
        skipCars:遍历该车道时，跳过车道尾部0或1辆车；0就是正常情况；1是因为下一道路限速太低或没有空位导
        致本应通过路口的尾部车辆未能通过路口，该车辆将行驶到当前道路的最前端，并置为终止状态，因此在本过程中
        应跳过该车辆；
        '''
        lane = self.lanes[direction][laneNo]
        carNum = len(lane)     #该车道上的车辆数目
        roadEnd = self.roadLen+1-skipCars     #车辆能行驶到的最大位置，可能是道路的尽头，也可能是前一辆车的位置
        statusAhead = 1-skipCars     #该车辆前方车辆的状态，1代表waitting
        carsReachEnding = 0     #到达终点的车辆数目
        for i in range(carNum-(skipCars+1),-1,-1):
            #行驶速度为道路限速和车辆自身最大速度的较小者
            car = data.carDict[lane[i]]
            #如果该车辆仍未进入终止状态
            if not car.finish:
                speed = min(self.maxSpeed,car.maxSpeed)
                #假定按此速度行驶，可到达的位置为newPosition
                newPosition = car.position + speed
                #如果车辆驶出能行驶的最大位置，则继续等待，除非已到达终点
                if newPosition >= roadEnd:
                    if (car.getNextRoad() == -1) and (roadEnd == (self.roadLen + 1)):
                        carsReachEnding += 1
                        data.carsDoneNum += 1
                        car.done(timeNow)
                        car.endWaiting()
                    else:
                        if statusAhead == 1:
                            car.startWaiting()
                            roadEnd = car.position
                        else:
                            car.setPosition(roadEnd-1)
                            roadEnd = roadEnd-1
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
        self.updateCarSequeue(direction)
        #删除已经到达终点的车辆
        for i in range(carsReachEnding):
            lane.pop()

    def runCarInInitList(self,timeNow,priority,dire=2):
        #priority为True，只允许优先车辆上路;direction表示上路车辆进入道路的方向，1表示正向,0表示反向,2表示两个方向都变遍历；
        if dire == 1:
            directions = [1]
        elif dire == 0:
            if self.isDuplex:
                directions = [0]
            else:
                directions = []
        elif self.isDuplex:
            directions = [0,1]
        else:
            directions = [1]
        for direction in directions:
            #先计算该道路在该方向上各车道是否还有位置进入，求出能进入的车道数和能行驶的最大距离
            freeDistance = np.zeros(self.laneNum)
            statusAhead = []        #对应车道最后一辆车的状态
            for i in range(self.laneNum):
                if self.lanes[direction][i] == []:
                    freeDistance[i] = self.roadLen
                    statusAhead.append(True)
                else:
                    car = data.carDict[self.lanes[direction][i][0]]
                    freeDistance[i] = car.position-1
                    statusAhead.append(car.finish)
            laneNo = 0
            #先选择第一优先顺位的车进行是否能上路的判断，如果不是因为未到出发时间而无法上路，就要判断第二
            #优先顺位的车是否可以上路，以此类推，直到遇到因未到出发时间而无法上路的车
            priorityOrder = 1   
            while laneNo < self.laneNum:
                if freeDistance[laneNo] == 0:
                    laneNo += 1
                    continue
                if len(self.carInInitList[direction][0]) < priorityOrder:
                    break
                car = data.carDict[self.carInInitList[direction][0][-priorityOrder]]       #取对应顺位的优先车辆
                if car.setOffTime > timeNow:
                    break
                speed = min(car.maxSpeed,self.maxSpeed)
                if speed <= freeDistance[laneNo]:   #如果未被阻挡，直接进入道路
                    freeDistance[laneNo] = speed-1
                    self.carIn(car.carNo,laneNo,direction)
                    car.moveToNextRoad(speed,laneNo)
                    self.carInInitList[direction][0].pop(-priorityOrder)
                elif statusAhead[laneNo]:   #如果被阻挡，但前车是终止状态
                    self.carIn(car.carNo,laneNo,direction)
                    car.moveToNextRoad(freeDistance[laneNo],laneNo)
                    freeDistance[laneNo] = freeDistance[laneNo]-1
                    self.carInInitList[direction][0].pop(-priorityOrder)
                else:
                    priorityOrder += 1
            if not priority:
                priorityOrder = 1 
                while laneNo < self.laneNum:
                    if freeDistance[laneNo] == 0:
                        laneNo += 1
                        continue
                    if len(self.carInInitList[direction][1]) < priorityOrder:
                        break
                    car = data.carDict[self.carInInitList[direction][1][-priorityOrder]]       #取对应顺位的非优先车辆
                    if car.setOffTime > timeNow:
                        break
                    speed = min(car.maxSpeed,self.maxSpeed)
                    if speed <= freeDistance[laneNo]:   #如果未被阻挡，直接进入道路
                        freeDistance[laneNo] = speed-1
                        self.carIn(car.carNo,laneNo,direction)
                        car.moveToNextRoad(speed,laneNo)
                        self.carInInitList[direction][1].pop(-priorityOrder)
                    elif statusAhead[laneNo]:   #如果被阻挡，但前车是终止状态
                        self.carIn(car.carNo,laneNo,direction)
                        car.moveToNextRoad(freeDistance[laneNo],laneNo)
                        freeDistance[laneNo] = freeDistance[laneNo]-1
                        self.carInInitList[direction][1].pop(-priorityOrder)
                    else:
                        priorityOrder += 1
    
    def createCarSequeue(self,dire=2):
        '''
        构建等待车辆的优先级队列；
        '''
        if dire == 1:
            directions = [1]
        elif dire == 0:
            if self.isDuplex:
                directions = [0]
            else:
                directions = []
        elif self.isDuplex:
            directions = [0,1]
        else:
            directions = [1]
        for direction in directions:
            #依次遍历各车道最末尾waiting车辆，比较优先级，优先级高的排在列表尾部
            #遍历两遍，第一遍先给非优先车辆排序，第二遍再把优先车辆插入进入
            for laneNo in range(self.laneNum):
                for i in range(len(self.lanes[direction][laneNo])-1,-1,-1):
                    car = data.carDict[self.lanes[direction][laneNo][i]]
                    if car.finish: break
                    if not car.isPriority:
                        j = 0
                        while j < len(self.carSequeue[direction]):
                            carCurrent = data.carDict[self.carSequeue[direction][j]]
                            if car.carNo == carCurrent.carNo:
                                exit(1)
                            #现在队列里只有非优先车辆，而且是按照车道数从小到大，位置从大到小遍历的
                            #因此，车道数相同，一定是队列中的优先级高，车道不同时，位置大的优先级高
                            if car.laneNo == carCurrent.laneNo:
                                self.carSequeue[direction].insert(j,car.carNo)
                                break
                            elif car.position <= carCurrent.position:
                                self.carSequeue[direction].insert(j,car.carNo)
                                break
                            j += 1
                        if j == len(self.carSequeue[direction]):
                            self.carSequeue[direction].append(car.carNo)
            for laneNo in range(self.laneNum):
                for i in range(len(self.lanes[direction][laneNo])-1,-1,-1):
                    car = data.carDict[self.lanes[direction][laneNo][i]]
                    if car.finish: break
                    if car.isPriority:
                        j = 0
                        while j < len(self.carSequeue[direction]):
                            carCurrent = data.carDict[self.carSequeue[direction][j]]
                            #车道相同时，比较位置
                            if car.laneNo == carCurrent.laneNo:
                                if car.position < carCurrent.position:
                                    self.carSequeue[direction].insert(j,car.carNo)
                                    break
                            #车道不同时，按照优先车辆一定比非优先车辆的优先级高插入即可
                            #因为如果待插入优先车辆的车道数较小，优先级一定比非优先车辆高:
                            #如果该优先车辆前无非优先车辆阻挡，优先车辆优先级比其他车道的非优先车辆高；
                            #如果该优先车辆前有非优先车辆阻挡，该优先车辆的优先级在前方的非优先车辆之后，由上一种状况确定；
                            #如果待插入优先车辆的车道数大于队列中优先车辆的车道数，再比较位置
                            elif car.laneNo > carCurrent.laneNo and carCurrent.isPriority:
                                if car.position <= carCurrent.position:
                                    self.carSequeue[direction].insert(j,car.carNo)
                                    break
                            j += 1
                        if j == len(self.carSequeue[direction]):
                            self.carSequeue[direction].append(car.carNo)

    def getRoomOfTheEnd(self,direction):
        '''
        返回此道路某方向驶入道路端最左侧的有空位的车道的车道编号、空白距离以及最后一辆车的状态；
        '''
        endCarsStatus = True    #当道路满时，判断是否为终止满,True代表终止满
        for i in range(self.laneNum):
            if self.lanes[direction][i] == []:
                return (i,self.roadLen,False)
            carAtTheEnd = data.carDict[self.lanes[direction][i][0]]
            endCarsStatus = endCarsStatus and carAtTheEnd.finish
            if carAtTheEnd.position > 1:
                return (i,carAtTheEnd.position-1,carAtTheEnd.finish)
        return (None,None,endCarsStatus)

    def updateCarSequeue(self,direction):
        '''
        删除队列中已经是终止状态的车辆；
        '''
        i = 0
        while True:
            if i >= len(self.carSequeue[direction]): break
            if data.carDict[self.carSequeue[direction][i]].finish:
                self.carSequeue[direction].pop(i)
            else:
                i += 1
    
    def getCarFromSequeue(self,direction):
        '''
        获得当前道路在当前方向上优先级最高的等待车辆；
        '''
        if bool(self.carSequeue[direction]):
            return self.carSequeue[direction][-1]
        else:
            return None

    def popCarFromSequeue(self,direction):
        '''
        当前道路在当前方向上优先级最高的车辆进入终止状态之后，从队列中删除；
        '''
        self.carSequeue[direction].pop()

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
        在每次开始调度路口的车辆时，给每个路口的等待的车辆进行优先级排序;
        '''
        for roadNo in self.roads:
            if roadNo != -1:
                data.roadDict[roadNo].createCarSequeue(dire=self.roadsDirections[roadNo])

    def updateRoads(self,timeNow):
        '''
        按照id从小到大的顺序遍历道路；
        '''
        roadsDoneNum = 0
        for roadNo in sorted(self.roads):
            if roadNo == -1: 
                roadsDoneNum += 1
                continue
            direction = self.roadsDirections[roadNo]
            road = data.roadDict[roadNo]
            while True:
                carNo = road.getCarFromSequeue(direction)
                if carNo == None: 
                    roadsDoneNum += 1
                    break
                car = data.carDict[carNo]
                if car.getNextRoad() == -1:  #当前车辆即将到达终点，视为直行，在道路内的函数进行处理
                    car.setWaitingFather(None)
                    road.updateCars(timeNow,direction,car.laneNo)
                else:
                    turnDirection = self.DLR.value(roadNo,car.getNextRoad())  #1:直行，2：左转，3：右转
                    #判断是否与其他道路上的第一优先级车辆冲突
                    conflict = False
                    for otherRoadNo in self.roads:
                        if otherRoadNo == -1 or otherRoadNo == roadNo: continue
                        otherCarNo = data.roadDict[otherRoadNo].getCarFromSequeue(self.roadsDirections[otherRoadNo])
                        if otherCarNo == None: continue
                        otherCar = data.carDict[otherCarNo]
                        if otherCar.getNextRoad() != car.getNextRoad(): continue
                        if otherCar.isPriority and (not car.isPriority):
                            car.setWaitingFather(otherCarNo)
                            conflict = True
                            break
                        elif (not otherCar.isPriority) and car.isPriority:
                            continue
                        otherTurnDirection = self.DLR.value(otherRoadNo,otherCar.getNextRoad())
                        if otherTurnDirection < turnDirection: 
                            car.setWaitingFather(otherCarNo)
                            conflict = True
                            break
                    if conflict: break
                    #判断是否能顺利进行转向
                    nextRoad = data.roadDict[car.getNextRoad()]
                    distanceOnNextRoad = min(nextRoad.maxSpeed,car.maxSpeed)-(road.roadLen-car.position)    #在下一道路应行使的距离
                    if distanceOnNextRoad <= 0:     #不得通过路口，只能前进到当前道路的最前端
                        car.setPosition(road.roadLen)
                        car.endWaiting()
                        road.updateCars(timeNow,direction,car.laneNo,skipCars=1)
                    else:
                        #判断是否能驶入下一道路最左侧的有空位的车道
                        nextRoadDirection = 1-self.roadsDirections[nextRoad.roadNo]
                        nextRoadLaneNo,nextRoadFreeDistance,nextRoadStatus = nextRoad.getRoomOfTheEnd(nextRoadDirection)
                        if nextRoadLaneNo == None: 
                            if nextRoadStatus:  #终止满
                                car.setPosition(road.roadLen)
                                car.endWaiting()
                                road.updateCars(timeNow,direction,car.laneNo,skipCars=1)
                            else:
                                break
                        elif nextRoadFreeDistance >= distanceOnNextRoad:
                            preLaneNo = car.laneNo
                            car.moveToNextRoad(distanceOnNextRoad,nextRoadLaneNo)
                            car.endWaiting()
                            road.carOut(preLaneNo,direction)
                            road.updateCars(timeNow,direction,preLaneNo)
                            nextRoad.carIn(car.carNo,nextRoadLaneNo,nextRoadDirection)
                            nextRoad.runCarInInitList(timeNow,True,dire=nextRoadDirection)
                        elif nextRoadStatus == True:
                            preLaneNo = car.laneNo
                            car.moveToNextRoad(nextRoadFreeDistance,nextRoadLaneNo)
                            car.endWaiting()
                            road.carOut(preLaneNo,direction)
                            road.updateCars(timeNow,direction,preLaneNo)
                            nextRoad.carIn(car.carNo,nextRoadLaneNo,nextRoadDirection)
                            nextRoad.runCarInInitList(timeNow,True,dire=nextRoadDirection)
                        else:
                            break
        if roadsDoneNum == 4:
            return 1
        else:
            return 0

class Car():

    def __init__(self,carNo=None,fromId=None,toId=None,maxSpeed=None,planTime=None,isPriority=0,isPreset=0):
        self.carNo = carNo          #车辆编号
        self.fromId = fromId        #出发地路口编号
        self.toId = toId            #目的地路口编号
        self.maxSpeed = maxSpeed    #车辆自身最大速度
        self.planTime = planTime    #车辆计划出发时间
        self.waiting = False        #该车辆是否处于等待状态，True代表处于等待状态
        #处于等待状态时，等待的原因；None表示原因尚未确定或前方无等待车辆，因要通过路口而进入等待
        #当前方有等待车辆时，father就是前方等待车辆的编号
        self.waitingFather = None
        self.finish = True         #True代表该车进入终止状态
        self.position = -1          #该车辆在车道上的位置,取值范围为[1,roadLen]
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
        self.waitingFather = None

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

    def setWaitingFather(self,firstFather):
        self.waitingFather = firstFather
        #设置在等待的车辆，并检查是否有环路
        father = firstFather
        while father != None:
            #如果在上溯过程中找到了自己，则说明存在环
            if father == self.carNo:
                #打印出环路信息
                logging.info('Car: %d, Road: %d' % (self.carNo,self.roadNo))
                father = firstFather
                while True:
                    fatherCar = data.carDict[father]
                    logging.info('Car: %d, Road: %d' % (father,fatherCar.roadNo))
                    if father == self.carNo:
                        break
                exit('Dead lock!')
            father = data.carDict[father].waitingFather

    def done(self,timeNow):
        data.allScheduleTime += timeNow-self.planTime
        data.scheduleTime = timeNow
        if self.isPriority:
            data.allPriorityScheduleTime += timeNow-self.planTime
            data.priorityScheduleTime = timeNow

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