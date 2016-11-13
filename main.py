import sys
import math
import copy
import itertools
import queue
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

        x.draw(painter, label.height())

    painter.end()
    label.clear()
    label.setPixmap(pixmap)

def collision_test():
    for item_pair in itertools.combinations(range(len(items)), 2):
        if Item.collision(items[item_pair[0]], items[item_pair[1]]):
            print('collision: {}, {}'.format(*item_pair))

def build_pfield(label, start, draw=False):
    height = label.height()
    width = label.width()

    #draw pfield
    def draw_pfield():
        image = QImage(width, height, QImage.Format_RGB32)
        for i in range(width):
            for j in range(height):
                image.setPixelColor(i, j, QColor(*([255.0 * pfield[i][(j+1) * -1]/max_potential]*3)))

        label.clear()
        label.setPixmap(QPixmap(image))

    #extend function
    neighbor = [[0, 1], [0, -1], [1, 0], [-1, 0]]
    def extend(x, y):
        for i in neighbor:
            nx = x+i[0]
            ny = y+i[1]
            if height > nx >= 0 and width > ny >= 0 and pfield[nx][ny] is -1:
                pfield[nx][ny] = pfield[x][y] + 1
                q.put([nx, ny])
                nonlocal max_potential
                if pfield[nx][ny] > max_potential:
                    max_potential = pfield[nx][ny]

    t = time.time()

    #init pfield
    pfield = [[-1 for _ in range(height)] for _ in range(width)]

    #draw obstacle
    for item in items:
        if type(item) is Obstacle:
            item.draw_pfield(pfield)

    #set goal
    max_potential = 1
    pfield[int(start.x)][int(start.y)] = 0

    q = queue.Queue()
    q.put([int(start.x), int(start.y)])
    while not q.empty():
        extend(*(q.get()))

    for i in range(width):
        for j in range(height):
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

    #extend function
    neighbor = [[0, 0, 1], [0, 0, -1], [0, 1, 0], [0, -1, 0], [1, 0, 0], [-1, 0, 0]]
    def extend(conf):
        if conf == goal:
            nonlocal done
            done = True

        else:
            for i in neighbor:
                new_conf = (conf[0]+i[0], conf[1]+i[1], (conf[2]+i[2])%360)
                if label.height() > new_conf[0] >= 0 and label.width() > new_conf[1] >= 0:
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
                                if not (label.height() > v.x >= 0 and label.width() > v.y >= 0):
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
        pfields.append(build_pfield(label, x.transform(items[n*2+1].conf())))

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
        mouse_press = {'button': event.button(), 'x': event.x(), 'y': self.height() - event.y()}

        #detect selected item
        global selected
        for i in range(len(items)):
            if items[i].contains(float(event.x()), float(self.height() - event.y())):
                selected = i
                break
        else:
            selected = -1

        print('Mouse {} press at ({}, {}), item {} selected.'.format(event.button(), event.x(), self.height() - event.y(), selected))

    def mouseMoveEvent(self, event):
        #calc temp_conf and update label
        if selected is not -1:
            #translate
            if mouse_press['button'] == Qt.LeftButton:
                items[selected].temp_conf = [event.x() - mouse_press['x'], (self.height() - event.y()) - mouse_press['y'], 0.0]

            #rotate
            elif mouse_press['button'] == Qt.RightButton:
                angle_new = math.atan2((self.height() - event.y()) - items[selected].init_conf[1], event.x() - items[selected].init_conf[0])
                angle_old = math.atan2(mouse_press['y'] - items[selected].init_conf[1], mouse_press['x'] - items[selected].init_conf[0])
                items[selected].temp_conf = [0.0, 0.0, math.degrees(angle_new - angle_old)]

            draw_data(self)

    def mouseReleaseEvent(self, event):
        print('Mouse {} release at ({}, {})'.format(event.button(), event.x(), self.height() - event.y()))
        #save temp_conf to init_conf and reset
        if selected is not -1:
            items[selected].init_conf = items[selected].conf()
            items[selected].temp_conf = [0.0, 0.0, 0.0]
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
