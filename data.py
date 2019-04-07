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

#总调度时间
allPriorityScheduleTime = 0
allScheduleTime = 0