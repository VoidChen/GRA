import copy
import queue
import time
import random
from obj import *
from pfield import *
from PyQt5.QtWidgets import *

#validity test
def validity_test(robot, scene, width, height):
    #collision test
    for obstacle in scene.obstacle:
        if sum([(robot.init_conf[i] - obstacle.init_conf[i])**2 for i in range(2)])**0.5 <= robot.radius + obstacle.radius:
            if Item.collision(robot, obstacle):
                return False

    for robot_init in scene.robot_init:
        if robot_init.index != robot.index:
            if sum([(robot.init_conf[i] - robot_init.init_conf[i])**2 for i in range(2)])**0.5 <= robot.radius + robot_init.radius:
                if Item.collision(robot, robot_init):
                    return False

    #boundary test
    for poly in robot.polygons:
        for v in poly.configured(robot.conf()).vertices:
            if not (height > v.x >= 0 and width > v.y >= 0):
                return False

    return True


def find_path(scene, robot_index, width, height):
    def calc_pvalue(conf):
        sum = 0
        for i in range(len(robot.controls)):
            temp = robot.controls[i].transform(conf)
            sum += pfields[i][int(temp.x)][int(temp.y)]
        return sum
    def extend(conf):
        if conf == goal:
            return True

        else:
            for i in neighbor:
                new_conf = (conf[0]+i[0], conf[1]+i[1], (conf[2]+i[2])%360)
                if new_conf not in valid and height > new_conf[0] >= 0 and width > new_conf[1] >= 0:
                    robot.init_conf = new_conf
                    valid[new_conf] = validity_test(robot, scene, width, height)
                    if valid[new_conf]:
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
    robot = copy.deepcopy(scene.robot_init[robot_index])
    neighbor = [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]]

    #build pfields
    pfields = []
    for i in range(len(robot.controls)):
        pfields.append(build_pfield(scene, [robot_index, i], width, height))

    #init heap and cspace
    heap = queue.PriorityQueue()
    valid = {}
    prev_conf = {}

    #set init and goal
    init_conf = [int(x) for x in scene.robot_init[robot_index].init_conf]
    goal_conf = [int(x) for x in scene.robot_goal[robot_index].init_conf]
    init_conf[2] %= 360
    goal_conf[2] %= 360
    init = tuple(init_conf)
    goal = tuple(goal_conf)
    print('init:', init)
    print('goal:', goal)

    #extend
    valid[init] = True
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
        return backtrace(goal), valid
    else:
        print('Fail...')
        return [], valid

def straight_path(start, end):
    diff = [e-s for s, e in zip(start, end)]
    absdiff = [x if x > 0 else -x for x in diff]
    steps = []
    for i in range(3):
        sign = 1 if diff[i] > 0 else -1
        steps += [(i, sign) for _ in range(absdiff[i])]

    random.shuffle(steps)

    result = [start[:]]
    current = list(start)
    for step in steps:
        current[step[0]] += step[1]
        result.append(tuple(current))

    return result

def path_validity_test(path, valid, robot, scene, width, height):
    for conf in path:
        if conf not in valid:
            robot.init_conf = conf
            valid[conf] = validity_test(robot, scene, width, height)

        if not valid[conf]:
            return False

    return True

def smooth_path(path, valid, scene, robot_index, width, height):
    sp = straight_path(path[0], path[-1])
    if len(sp) < len(path):
        robot = copy.deepcopy(scene.robot_init[robot_index])
        if path_validity_test(sp, valid, robot, scene, width, height):
            return sp
        else:
            first = smooth_path(path[:len(path)//2], valid, scene, robot_index, width, height)
            second = smooth_path(path[len(path)//2:], valid, scene, robot_index, width, height)
            return first + second
    else:
        return path
