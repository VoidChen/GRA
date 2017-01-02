import copy
from obj import *

def read_robot(filename):
    data = []
    with open(filename, 'r')as fread:
        for line in fread:
            if not line.startswith('#'):
                data += line.split()

    robots = []
    for i in range(int(data.pop(0))):
        robots.append(Robot(data))
        robots[-1].index = i

    return robots

def read_obstacle(filename):
    data = []
    with open(filename, 'r')as fread:
        for line in fread:
            if not line.startswith('#'):
                data += line.split()

    obstacles = []
    for i in range(int(data.pop(0))):
        obstacles.append(Obstacle(data))
        obstacles[-1].index = i

    return obstacles

def read_data(robot_filename, obstacle_filename):
    #init
    scene = Scene()

    #read robot
    scene.robot_init += read_robot(robot_filename)
    scene.robot_num = len(scene.robot_init)
    for robot in scene.robot_init:
        scene.robot_goal.append(copy.deepcopy(robot))
        scene.robot_goal[-1].init_conf = scene.robot_goal[-1].goal_conf

    #read obstacle
    scene.obstacle += read_obstacle(obstacle_filename)
    scene.obstacle_num = len(scene.obstacle)

    return scene
