import sys
import math
import copy
import itertools
import queue
import heapq
import time
from obj import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

items = []

def read_data():
    #robot.dat
    data = []
    with open('robot.dat', 'r')as fread:
        for line in fread:
            if not line.startswith('#'):
                data += line.split()

    robot_num = int(data.pop(0))
    robots = []
    for _ in range(robot_num):
        robots.append(Robot(data))

    #obstacle.dat
    data = []
    with open('obstacle.dat', 'r')as fread:
        for line in fread:
            if not line.startswith('#'):
                data += line.split()

    obstacle_num = int(data.pop(0))
    obstacles = []
    for _ in range(obstacle_num):
        obstacles.append(Obstacle(data))

    #combine to items list
    global items
    items = []
    for x in robots:
        items.append(x)
        items[-1].type = 'init'

        items.append(copy.deepcopy(x))
        items[-1].init_conf = x.goal_conf
        items[-1].type = 'goal'

    for x in obstacles:
        items.append(x)

def scale_data(scale):
    for x in items:
        x.scale(scale)

def read_and_scale(scale):
    read_data()
    scale_data(scale)

def draw_data(label):
    pixmap = QPixmap(label.width(), label.height())
    pixmap.fill(Qt.black)
    painter = QPainter(pixmap)

    for x in items:
        if type(x) is Robot:
            if x.type is 'init':
                painter.setPen(QPen(QColor(0, 255, 0), 1))
            elif x.type is 'goal':
                painter.setPen(QPen(QColor(0, 255, 255), 1))
        elif type(x) is Obstacle:
            painter.setPen(QPen(QColor(255, 0, 0), 1))
        else:
            painter.setPen(QPen(QColor(255, 255, 255), 1))

        x.draw(painter)

    painter.end()
    label.clear()
    label.setPixmap(pixmap)

def collision_test():
    for item_pair in itertools.combinations(range(len(items)), 2):
        if Item.collision(items[item_pair[0]], items[item_pair[1]]):
            print('collision: {}, {}'.format(*item_pair))

def build_pfield(label, start, draw=False):
    #draw pfield
    def draw_pfield():
        image = QImage(label.width(), label.height(), QImage.Format_RGB32)
        for i in range(label.width()):
            for j in range(label.height()):
                image.setPixelColor(i, j, QColor(*([255.0 * pfield[i][j]/max_potential]*3)))

        label.clear()
        label.setPixmap(QPixmap(image))

    #extend function
    neighbor = [[0, 1], [0, -1], [1, 0], [-1, 0]]
    def extend(x, y):
        for i in neighbor:
            nx = x+i[0]
            ny = y+i[1]
            if label.height() > nx >= 0 and label.width() > ny >= 0 and pfield[nx][ny] is -1:
                pfield[nx][ny] = pfield[x][y] + 1
                q.put([nx, ny])

    t = time.time()

    #init pfield
    pfield = [[-1 for _ in range(label.height())] for _ in range(label.width())]

    #draw obstacle
    for item in items:
        if type(item) is Obstacle:
            item.draw_pfield(pfield)

    #set goal
    pfield[int(start.x)][int(start.y)] = 0

    max_potential = 1
    q = queue.Queue()
    q.put([int(start.x), int(start.y)])
    while not q.empty():
        x, y = q.get()
        extend(x, y)
        if pfield[x][y] > max_potential:
            max_potential = pfield[x][y]

    for i in range(label.width()):
        for j in range(label.height()):
            if pfield[i][j] < 0:
                pfield[i][j] = max_potential * 1.5
    max_potential *= 1.5

    print('Build potential field used time:', time.time() - t)

    if draw:
        draw_pfield()

    return pfield

def pfield_box_update(box):
    box.clear()
    box.addItem('No potential field')
    for i in range(1, len(items), 2):
        if type(items[i]) is Robot:
            for j in range(len(items[i].controls)):
                box.addItem('Robot {} ControlPoint {}'.format(int(i/2), j), QVariant([i, j]))
        else:
            break

def pfield_box_changed(box, label):
    if box.currentIndex() is not 0:
        rc = box.currentData()
        build_pfield(label, items[rc[0]].controls[rc[1]].transform(items[rc[0]].conf()), True)
    else:
        draw_data(label)

def find_path(label, n):
    def calc_pvalue(conf):
        sum = 0
        for i in range(len(robot.controls)):
            temp = robot.controls[i].transform(conf)
            sum += pfields[i][int(temp.x)][int(temp.y)]
        return sum

    #heap function
    def push(conf):
        pvalue = calc_pvalue(conf)
        heapq.heappush(heap, (pvalue, conf))

    def pop():
        return heapq.heappop(heap)

    #extend function
    neighbor = [[0, 0, 1], [0, 0, -1], [0, 1, 0], [0, -1, 0], [1, 0, 0], [-1, 0, 0]]
    def extend(x, y, z):
        if visit[x][y][z] is -1:
            nonlocal done
            done = True

        else:
            for i in neighbor:
                nx, ny, nz = x+i[0], y+i[1], (z+i[2])%360
                if label.height() > nx >= 0 and label.width() > ny >= 0:
                    if visit[nx][ny][nz] is not 1:
                        #check conf validity
                        robot.init_conf = [nx, ny, nz]
                        valid = True
                        for item in items:
                            if type(item) is Obstacle and Item.collision(robot, item):
                                valid = False
                                break
                        for poly in robot.polygons:
                            for v in poly.configured(robot.conf()).vertices:
                                if not (label.height() > v.x >= 0 and label.width() > v.y >= 0):
                                    valid = False
                                    break
                            if not valid:
                                break

                        if valid:
                            if visit[nx][ny][nz] is 0:
                                visit[nx][ny][nz] = 1
                            prev_conf[(nx, ny, nz)] = [x, y, z]
                            push([nx, ny, nz])

    def backtrace(conf):
        if tuple(conf) in prev_conf:
            return backtrace(prev_conf[tuple(conf)]) + [conf]
        else:
            return [conf]

    t = time.time()

    #copy robot
    robot = copy.deepcopy(items[n*2])

    #build pfields
    pfields = []
    for x in robot.controls:
        pfields.append(build_pfield(label, x.transform(items[n*2+1].conf())))

    #init heap and cspace
    heap = []
    visit = [[[0 for _ in range(360)] for _ in range(label.height())] for _ in range(label.width())]
    prev_conf = {}

    #set init and goal
    init = [int(items[n*2].init_conf[x]) for x in range(3)]
    init[2] %= 360
    visit[init[0]][init[1]][init[2]] = 1
    goal = [int(items[n*2+1].init_conf[x]) for x in range(3)]
    goal[2] %= 360
    visit[goal[0]][goal[1]][goal[2]] = -1
    print('init:', init)
    print('goal:', goal)

    push(init)

    done = False

    while not done and len(heap) is not 0:
        temp = pop()
        #print('extend', temp)
        extend(*(temp[1]))

    if done:
        print('Find path!')
    else:
        print('Fail...')

    print('Find path used time:', time.time() - t)

    path = backtrace(goal)
    return path

def show_path(label, n, total_time = 5):
    path = find_path(label, n)
    delay = total_time / len(path)
    label.clear()
    for conf in path:
        items[n*2].init_conf = conf
        draw_data(label)
        QApplication.processEvents()
        time.sleep(delay)

class CustomLabel(QLabel):
    def __init__(self, parent=None, flags=Qt.WindowFlags()):
        super(CustomLabel, self).__init__(parent, flags)

    def mousePressEvent(self, event):
        #save press button&point
        global mouse_press
        mouse_press = {'button': event.button(), 'x': event.x(), 'y': event.y()}

        #detect selected item
        global selected
        for i in range(len(items)):
            if items[i].contains(float(event.x()), float(event.y())):
                selected = i
                break
        else:
            selected = -1

        print('Mouse {} press at ({}, {}), item {} selected.'.format(event.button(), event.x(), event.y(), selected))

    def mouseMoveEvent(self, event):
        #calc temp_conf and update label
        if selected is not -1:
            #translate
            if mouse_press['button'] == Qt.LeftButton:
                items[selected].temp_conf = [event.x() - mouse_press['x'], event.y() - mouse_press['y'], 0.0]

            #rotate
            elif mouse_press['button'] == Qt.RightButton:
                angle_new = math.atan2(event.y() - items[selected].init_conf[1], event.x() - items[selected].init_conf[0])
                angle_old = math.atan2(mouse_press['y'] - items[selected].init_conf[1], mouse_press['x'] - items[selected].init_conf[0])
                items[selected].temp_conf = [0.0, 0.0, math.degrees(angle_new - angle_old)]

            draw_data(self)

    def mouseReleaseEvent(self, event):
        #save temp_conf to init_conf and reset
        if selected is not -1:
            items[selected].init_conf = items[selected].conf()
            items[selected].temp_conf = [0.0, 0.0, 0.0]
        print('Mouse {} release at ({}, {})'.format(event.button(), event.x(), event.y()))
        print('item {} new conf {}'.format(selected, items[selected].conf()))

if __name__ == '__main__':
    #init
    width = 400
    height = 400
    scale = 400/128
    app = QApplication(sys.argv)

    #main widget
    widget = QWidget()
    widget.resize(width, height)
    widget.setWindowTitle('GRA')
    widget.show()

    #label
    label = CustomLabel()
    label.resize(width, height)
    draw_data(label)

    #button
    btn_read = QPushButton('Read data')
    btn_read.resize(100, 50)
    btn_read.clicked.connect(lambda: read_and_scale(scale))
    btn_read.clicked.connect(lambda: pfield_box_update(box_pfield))
    btn_read.show()

    btn_draw = QPushButton('Draw data')
    btn_draw.resize(100, 50)
    btn_draw.clicked.connect(lambda: draw_data(label))
    btn_draw.clicked.connect(lambda: box_pfield.setCurrentIndex(0))
    btn_draw.show()

    btn_find_path = QPushButton('Find path')
    btn_find_path.resize(100, 50)
    btn_find_path.clicked.connect(lambda: find_path(label, 0))
    btn_find_path.show()

    btn_show_path = QPushButton('Show path')
    btn_show_path.resize(100, 50)
    btn_show_path.clicked.connect(lambda: show_path(label, 0))
    btn_show_path.show()

    #combobox
    box_pfield = QComboBox()
    box_pfield.resize(100, 50)
    box_pfield.activated.connect(lambda: pfield_box_changed(box_pfield, label))
    box_pfield.show()

    #layout
    layout_btn = QHBoxLayout()
    layout_btn.addWidget(btn_read)
    layout_btn.addWidget(btn_draw)
    layout_btn.addWidget(btn_find_path)
    layout_btn.addWidget(btn_show_path)

    layout = QVBoxLayout()
    layout.addWidget(label)
    layout.addLayout(layout_btn)
    layout.addWidget(box_pfield)

    widget.setLayout(layout)

    app.exec()
