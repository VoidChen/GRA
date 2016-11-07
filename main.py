import sys
import math
import copy
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

        print('Mouse at ({}, {})'.format(event.x(), event.y()))

    def mouseReleaseEvent(self, event):
        #save temp_conf to init_conf and reset
        if selected is not -1:
            items[selected].init_conf = items[selected].conf()
            items[selected].temp_conf = [0.0, 0.0, 0.0]
        print('Mouse {} release at ({}, {})'.format(event.button(), event.x(), event.y()))

if __name__ == '__main__':
    width = 600
    height = 400
    scale = 3
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
    btn_read.show()

    btn_draw = QPushButton('Draw data')
    btn_draw.resize(100, 50)
    btn_draw.clicked.connect(lambda: draw_data(label))
    btn_draw.show()

    #layout
    layout_btn = QHBoxLayout()
    layout_btn.addWidget(btn_read)
    layout_btn.addWidget(btn_draw)

    layout = QVBoxLayout()
    layout.addWidget(label)
    layout.addLayout(layout_btn)

    widget.setLayout(layout)

    app.exec()
