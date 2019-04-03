#用于存放路口信息的字典和列表
crossDict = dict()         
crossList = list()
newCrossNoToOrigiNo = dict()    #路口的新编号到原编号的映射
#用于存放道路信息的字典和列表
roadDict = dict()     
roadList = list()
#用于存放车辆信息的字典和列表
carDict = dict()    
carList = list()

#索引两个路口之间的道路编号的二维字典，在读完路口和道路数据之后进行初始化
roadBetweenCrosses = None

#从每个路口出发的车辆的列表，用二维列表存储
carsFromEachCross = None
carsToEachCross = None

#路口的地图
crossMap = None