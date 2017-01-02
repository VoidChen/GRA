import sys
import math
import time
from obj import *
from pfield import *
from path import *
from data import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

scene = Scene()

def draw_data(label, width_c, height_c, scale):
    pixmap = QPixmap(width_c, height_c)
    pixmap.fill(Qt.black)
    painter = QPainter(pixmap)

    for x in scene.obstacle:
        painter.setPen(QPen(QColor(255, 0, 0), 1))
        x.draw(painter, height_c, scale)

    for x in scene.robot_goal:
        painter.setPen(QPen(QColor(0, 128, 255), 1))
        x.draw(painter, height_c, scale)

    for x in scene.robot_init:
        painter.setPen(QPen(QColor(0, 255, 0), 1))
        x.draw(painter, height_c, scale)

    painter.end()
    label.clear()
    label.setPixmap(pixmap)

def read_and_draw(label, width_c, height_c, scale):
    global scene
    scene = read_data('robot.dat', 'obstacle.dat')
    draw_data(label, width_c, height_c, scale)

def pfield_box_update(box, scene):
    box.clear()
    box.addItem('No potential field')
    for i in range(scene.robot_num):
        for j in range(len(scene.robot_init[i].controls)):
            box.addItem('Robot {} ControlPoint {}'.format(i, j), QVariant([i, j]))

def pfield_box_changed(box, label, scene, width_c, height_c):
    if box.currentIndex() is not 0:
        rc = box.currentData()
        pfield = build_pfield(scene, rc, width_c, height_c, scale)
        draw_pfield(label, pfield, width_c, height_c)
    else:
        draw_data(label, width_c, height_c, scale)

def show_path(robot_index, label, total_time = 5):
    path = find_path(scene, robot_index, width, height)
    if len(path) is not 1:
        path.append(tuple(scene.robot_init[robot_index].init_conf))
        delay = total_time / len(path)
        for conf in path:
            scene.robot_init[robot_index*2].init_conf = conf
            draw_data(label, width_c, height_c, scale)
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
        selected = None
        for i in range(len(scene.items)):
            for j in range(len(scene.items[i])):
                if scene.items[i][j].contains(float(event.x()/scale), float((self.height() - event.y())/scale)):
                    selected = (i, j)
                    break
            if selected != None:
                break

        print('Mouse {} press at ({}, {}), item {} selected.'.format(event.button(), event.x(), self.height() - event.y(), selected))


    def mouseMoveEvent(self, event):
        def rotate_degree(item_x, item_y, old_x, old_y, new_x, new_y):
            angle_new = math.atan2(new_y - item_y, new_x - item_x)
            angle_old = math.atan2(old_y - item_y, old_x - item_x)
            return math.degrees(angle_new - angle_old)

        #calc temp_conf and update label
        if selected is not None:
            #translate
            if mouse_press['button'] == Qt.LeftButton:
                scene.items[selected[0]][selected[1]].temp_conf = [(event.x() - mouse_press['x'])/scale, ((self.height() - event.y()) - mouse_press['y'])/scale, 0.0]

            #rotate
            elif mouse_press['button'] == Qt.RightButton:
                item_xy = (scene.items[selected[0]][selected[1]].init_conf[0], scene.items[selected[0]][selected[1]].init_conf[1])
                old_xy = (mouse_press['x']/scale, mouse_press['y']/scale)
                new_xy = (event.x()/scale, (self.height() - event.y())/scale)
                scene.items[selected[0]][selected[1]].temp_conf = [0.0, 0.0, rotate_degree(*item_xy, *old_xy, *new_xy)]

            #update canvas
            draw_data(label, width_c, height_c, scale)

    def mouseReleaseEvent(self, event):
        print('Mouse {} release at ({}, {})'.format(event.button(), event.x(), self.height() - event.y()))
        #save temp_conf to init_conf and reset
        if selected is not None:
            scene.items[selected[0]][selected[1]].init_conf = scene.items[selected[0]][selected[1]].conf()
            scene.items[selected[0]][selected[1]].temp_conf = [0.0, 0.0, 0.0]
            print('item {} new conf {}'.format(selected, scene.items[selected[0]][selected[1]].conf()))

if __name__ == '__main__':
    #init
    width = 128
    height = 128
    width_c = 400
    height_c = 400
    scale = width_c/width
    app = QApplication(sys.argv)

    #main widget
    widget = QWidget()
    widget.resize(width, height)
    widget.setWindowTitle('GRA')
    widget.show()

    #label
    label = CustomLabel()
    label.resize(width_c, height_c)
    draw_data(label, width_c, height_c, scale)

    #button
    btn_read = QPushButton('Read data')
    btn_read.resize(100, 50)
    btn_read.clicked.connect(lambda: read_and_draw(label, width_c, height_c, scale))
    btn_read.clicked.connect(lambda: pfield_box_update(box_pfield, scene))
    btn_read.show()

    btn_show_path = QPushButton('Show path')
    btn_show_path.resize(100, 50)
    btn_show_path.clicked.connect(lambda: show_path(0, label))
    btn_show_path.show()

    #combobox
    box_pfield = QComboBox()
    box_pfield.resize(100, 50)
    box_pfield.activated.connect(lambda: pfield_box_changed(box_pfield, label, scene, width_c, height_c))
    box_pfield.show()

    #layout
    layout_btn = QHBoxLayout()
    layout_btn.addWidget(btn_read)
    layout_btn.addWidget(btn_show_path)

    layout = QVBoxLayout()
    layout.addWidget(label)
    layout.addLayout(layout_btn)
    layout.addWidget(box_pfield)

    widget.setLayout(layout)

    app.exec()
