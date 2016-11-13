import copy
import queue
import time
from obj import *
from pfield import *
from PyQt5.QtWidgets import *

def find_path(items, n, height, width):
    def calc_pvalue(conf):
        sum = 0
        for i in range(len(robot.controls)):
            temp = robot.controls[i].transform(conf)
            sum += pfields[i][int(temp.x)][int(temp.y)]
        return sum

    #extend function
    neighbor = [[0, 0, 1], [0, 0, -1], [0, 1, 0], [0, -1, 0], [1, 0, 0], [-1, 0, 0]]
    def extend(conf):
        if conf == goal:
            nonlocal done
            done = True

        else:
            for i in neighbor:
                new_conf = (conf[0]+i[0], conf[1]+i[1], (conf[2]+i[2])%360)
                if height > new_conf[0] >= 0 and width > new_conf[1] >= 0:
                    if new_conf not in visit:
                        #check conf validity
                        robot.init_conf = new_conf
                        valid = True
                        for item in items:
                            if type(item) is Obstacle and Item.collision(robot, item):
                                valid = False
                                break
                        for poly in robot.polygons:
                            for v in poly.configured(robot.conf()).vertices:
                                if not (height > v.x >= 0 and width > v.y >= 0):
                                    valid = False
                                    break
                            if not valid:
                                break

                        visit[new_conf] = True
                        if valid:
                            prev_conf[new_conf] = conf
                            heap.put((calc_pvalue(new_conf), new_conf))

    def backtrace(conf):
        if conf in prev_conf:
            return backtrace(prev_conf[conf]) + [conf]
        else:
            return [conf]

    t = time.time()

    #copy robot
    robot = copy.deepcopy(items[n*2])

    #build pfields
    pfields = []
    for x in robot.controls:
        pfields.append(build_pfield(items, x.transform(items[n*2+1].conf()), height, width))

    #init heap and cspace
    heap = queue.PriorityQueue()
    visit = {}
    prev_conf = {}

    #set init and goal
    init = (int(items[n*2].init_conf[0]), int(items[n*2].init_conf[1]), int(items[n*2].init_conf[2])%360)
    goal = (int(items[n*2+1].init_conf[0]), int(items[n*2+1].init_conf[1]), int(items[n*2+1].init_conf[2])%360)
    print('init:', init)
    print('goal:', goal)

    visit[init] = True
    heap.put((calc_pvalue(init), init))

    done = False

    while not done and not heap.empty():
        temp = heap.get()
        #print('extend', temp)
        extend(temp[1])

    print('Find path used time:', time.time() - t)

    if done:
        print('Find path!')
        return backtrace(goal)
    else:
        print('Fail...')
        return [init]
