import logging
import sys
import model
import buildData
import data
import method
import writeToFile
import time

logging.basicConfig(level=logging.DEBUG,
                    filename='log.log',
                    format='[%(asctime)s] %(levelname)s [%(funcName)s: %(filename)s, %(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filemode='a')


def main():
    if len(sys.argv) != 6:
        logging.info('please input args: car_path, road_path, cross_path, answerPath')
        exit(1)
        #car_path = 'config/car.txt'
        #road_path = 'config/road.txt'
        #cross_path = 'config/cross.txt'
        #answer_path = 'config/answer.txt'

    car_path = sys.argv[1]
    road_path = sys.argv[2]
    cross_path = sys.argv[3]
    preset_answer_path = sys.argv[4]
    answer_path = sys.argv[5]

    logging.info("car_path is %s" % (car_path))
    logging.info("road_path is %s" % (road_path))
    logging.info("cross_path is %s" % (cross_path))
    logging.info("preset_answer_path is %s" % (preset_answer_path))
    logging.info("answer_path is %s" % (answer_path))

    #读出数据并存储为对应的数据结构
    buildData.readData(road_path,car_path,cross_path,preset_answer_path)

    #method.dataVisualization('carsFromEachCross')
    #method.dataVisualization('carsToEachCross')
    #method.dataVisualization('roadLength')
    #method.dataVisualization('crossMap')

    method.getShortestPath()
    #method.dataVisualization('roadInPath')
    #method.dataVisualization('shortestPathLength')
    method.getSetOffTime()

    writeToFile.writeToAns(answer_path)

# to read input file
# process
# to write output file


if __name__ == "__main__":
    timeBegin = time.time()
    main()
    logging.info('Total time:%f' % (time.time()-timeBegin))