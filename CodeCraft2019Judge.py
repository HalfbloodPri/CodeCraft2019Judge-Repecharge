import logging
import sys
import model
import buildData
import data
import method
import time

logging.basicConfig(level=logging.DEBUG,
                    filename='log.log',
                    format='[%(asctime)s][%(funcName)s: %(filename)s, %(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filemode='a')


def main():
    if len(sys.argv) != 6:
        #logging.info('please input args: car_path, road_path, cross_path, answerPath')
        #exit(1)
        car_path = 'config/car.txt'
        road_path = 'config/road.txt'
        cross_path = 'config/cross.txt'
        preset_answer_path = 'config/presetAnswer.txt'
        answer_path = 'config/answer.txt'

    #car_path = sys.argv[1]
    #road_path = sys.argv[2]
    #cross_path = sys.argv[3]
    #preset_answer_path = sys.argv[4]
    #answer_path = sys.argv[5]

    buildData.readData(road_path,car_path,cross_path,preset_answer_path,answer_path)
    scheduleTime = 0
    while data.carsDoneNum < len(data.carList):
        method.runTheMap(scheduleTime)
        print('Time: %d' % scheduleTime)
        scheduleTime += 1
    print('Done.')
    logging.info('Schedule TIme: % d' % data.scheduleTime)
    logging.info('All Schedule Time: %d' % data.allScheduleTime)
    logging.info('Priority Schedule Time: %d' % (data.priorityScheduleTime-data.minPriorityPlanTime))
    logging.info('All Priority Schedule Time: %d' % data.allPriorityScheduleTime)


if __name__ == "__main__":
    logging.info(time.asctime())
    timeBegin = time.time()
    main()
    logging.info('Total time:%f' % (time.time()-timeBegin))