import sys
import math
import copy
import itertools
import queue
import time
from obj import *
from pfield import *
from path import *
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
        pfield = build_pfield(items, items[rc[0]].controls[rc[1]].transform(items[rc[0]].conf()), label.height(), label.width())
        draw_pfield(label, pfield)
    else:
        draw_data(label)

def show_path(n, label, total_time = 5):
    path = find_path(items, n, label.height(), label.width())
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
    btn_find_path.clicked.connect(lambda: find_path(items, 0, label.height(), label.width()))
    btn_find_path.show()

    btn_show_path = QPushButton('Show path')
    btn_show_path.resize(100, 50)
    btn_show_path.clicked.connect(lambda: show_path(0, label))
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
