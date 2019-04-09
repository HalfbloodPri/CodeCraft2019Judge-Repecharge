#用于存放路口信息的字典和列表
crossDict = dict()
crossList = list()
newCrossNoToOrigiNo = dict()    #路口的新编号到原编号的映射
origiCrossNoToNewNo = dict()    #路口的原编号到新编号的映射
#用于存放道路信息的字典和列表
roadDict = dict()     
roadList = list()
#用于存放车辆信息的字典和列表
carDict = dict()    
carList = list()
carsDoneNum = 0     #已经行驶完毕的车辆

#调度时间
priorityScheduleTime = 0
allPriorityScheduleTime = 0
scheduleTime = 0
allScheduleTime = 0

#用于计算系数的一些参数
priorityCarNum = 0
maxSpeed = 0
minSpeed = 100000
maxPrioritySpeed = 0
minPrioritySpeed = 100000
maxPlanTime = 0
minPlanTime = 100000
maxPriorityPlanTime = 0
minPriorityPlanTime = 100000    #优先车辆的最小计划出发时间
fromIds = dict()
toIds = dict()
priorityFromIds = dict()
priorityToIds = dict()
a = None
b = None