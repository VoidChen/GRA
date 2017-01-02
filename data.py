import copy
from obj import *

def read_robot(scene, filename):
    data = []
    with open(filename, 'r')as fread:
        for line in fread:
            if not line.startswith('#'):
                data += line.split()

    scene.robot_num = int(data.pop(0))

    scene.robot_init = []
    for i in range(scene.robot_num):
        scene.robot_init.append(Robot(data))
        scene.robot_init[-1].index = i

    scene.robot_goal = []
    for robot in scene.robot_init:
        scene.robot_goal.append(copy.deepcopy(robot))
        scene.robot_goal[-1].init_conf = scene.robot_goal[-1].goal_conf

    scene.items = [scene.robot_init, scene.robot_goal, scene.obstacle]

def read_obstacle(scene, filename):
    data = []
    with open(filename, 'r')as fread:
        for line in fread:
            if not line.startswith('#'):
                data += line.split()

    scene.obstacle_num = int(data.pop(0))
    scene.obstacle = []
    for i in range(scene.obstacle_num):
        scene.obstacle.append(Obstacle(data))
        scene.obstacle[-1].index = i

    scene.items = [scene.robot_init, scene.robot_goal, scene.obstacle]
