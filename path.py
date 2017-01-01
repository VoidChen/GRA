import copy
import queue
import time
from obj import *
from pfield import *
from PyQt5.QtWidgets import *

def find_path(items, robot_index, width, height):
    def calc_pvalue(conf):
        sum = 0
        for i in range(len(robot.controls)):
            temp = robot.controls[i].transform(conf)
            sum += pfields[i][int(temp.x)][int(temp.y)]
        return sum

    #validity test
    def valid(robot):
        #collision test
        for item in items:
            if type(item) is Obstacle and Item.collision(robot, item):
                return False
            if type(item) is Robot and item.type is 'init' and item.index != robot.index and Item.collision(robot, item):
                return False

        #boundary test
        for poly in robot.polygons:
            for v in poly.configured(robot.conf()).vertices:
                if not (height > v.x >= 0 and width > v.y >= 0):
                    return False

        return True

    def extend(conf):
        if conf == goal:
            return True

        else:
            for i in neighbor:
                new_conf = (conf[0]+i[0], conf[1]+i[1], (conf[2]+i[2])%360)
                if new_conf not in visit and height > new_conf[0] >= 0 and width > new_conf[1] >= 0:
                    visit[new_conf] = True
                    robot.init_conf = new_conf
                    if valid(robot):
                        prev_conf[new_conf] = conf
                        heap.put((calc_pvalue(new_conf), new_conf))
            return False

    #trace path
    def backtrace(conf):
        if conf in prev_conf:
            return backtrace(prev_conf[conf]) + [conf]
        else:
            return [conf]

    #init
    t = time.time()
    robot = copy.deepcopy(items[robot_index*2])
    neighbor = [[0, 0, 1], [0, 0, -1], [0, 1, 0], [0, -1, 0], [1, 0, 0], [-1, 0, 0]]

    #build pfields
    pfields = []
    for i in range(len(robot.controls)):
        pfields.append(build_pfield(items, [robot_index*2+1, i], width, height))

    #init heap and cspace
    heap = queue.PriorityQueue()
    visit = {}
    prev_conf = {}

    #set init and goal
    init = (int(items[robot_index*2].init_conf[0]), int(items[robot_index*2].init_conf[1]), int(items[robot_index*2].init_conf[2])%360)
    goal = (int(items[robot_index*2+1].init_conf[0]), int(items[robot_index*2+1].init_conf[1]), int(items[robot_index*2+1].init_conf[2])%360)
    print('init:', init)
    print('goal:', goal)

    #extend
    visit[init] = True
    heap.put((calc_pvalue(init), init))
    done = False

    while not done and not heap.empty():
        temp = heap.get()
        if extend(temp[1]):
            done = True
            break

    print('Find path used time:', time.time() - t)

    #trace path
    if done:
        print('Find path!')
        return backtrace(goal) + [tuple(items[robot_index*2+1].init_conf)]
    else:
        print('Fail...')
        return [init]
