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
target_index = 0
path_index = ([], -1)
valid_map = {}
robot_filename = 'robot.dat'
obstacle_filename = 'obstacle.dat'
pfield_enhance = False
pvalue_enhance = True

def load_robot():
    global robot_filename
    robot_filename = QFileDialog.getOpenFileName()[0]
    if robot_filename != '':
        read_robot(scene, robot_filename)

def load_obstacle():
    global obstacle_filename
    obstacle_filename = QFileDialog.getOpenFileName()[0]
    if obstacle_filename != '':
        read_obstacle(scene, obstacle_filename)

def reset():
    if robot_filename != '':
        read_robot(scene, robot_filename)
    if obstacle_filename != '':
        read_obstacle(scene, obstacle_filename)

def draw_data(label, width_c, height_c, scale, filename=''):
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

    if len(filename) > 0:
        pixmap.save(filename)

def target_box_update(box, scene):
    box.clear()
    for i in range(scene.robot_num):
        box.addItem('Target: Robot {}'.format(i), QVariant(i))

def target_box_changed(box):
    global target_index, path_index
    target_index = box.currentData()
    path_index = ([], -1)

def pfield_box_update(box, scene):
    box.clear()
    box.addItem('No potential field')
    for i in range(scene.robot_num):
        for j in range(len(scene.robot_init[i].controls)):
            box.addItem('Robot {} ControlPoint {}'.format(i, j), QVariant([i, j]))

    global target_index
    target_index = 0

def pfield_box_changed(box, label, scene, width_c, height_c):
    if box.currentIndex() is not 0:
        rc = box.currentData()
        pfield = build_pfield(scene, rc, width_c, height_c, scale, pfield_enhance)
        draw_pfield(label, pfield, width_c, height_c)
    else:
        draw_data(label, width_c, height_c, scale)

def pfield_enhance_box_changed(box):
    global pfield_enhance
    pfield_enhance = box.currentData()

def pvalue_enhance_box_changed(box):
    global pvalue_enhance
    pvalue_enhance = box.currentData()

def show_path(total_time = 5):
    path, robot_index = path_index
    if len(path) > 1:
        init = [tuple(scene.robot_goal[robot_index].init_conf)]
        goal = [tuple(scene.robot_init[robot_index].init_conf)]
        delay = total_time / len(path)
        for i, conf in enumerate(path + init + goal):
            scene.robot_init[robot_index].init_conf = conf
            draw_data(label, width_c, height_c, scale, 'image/path_{}.jpg'.format(i))
            QApplication.processEvents()
            time.sleep(delay)

def get_path():
    global path_index, valid_map
    path, valid_map = find_path(scene, target_index, width, height, border_extend=pfield_enhance, pvalue_enhance=pvalue_enhance)
    path_index = (path, target_index)
    show_path()

def path_smoothing():
    t = time.time()

    global path_index
    path, robot_index = path_index

    sp = path
    for _ in range(100):
        sp = smooth_path(sp, valid_map, scene, target_index, width, height)

    path_index = (sp, target_index)
    print('Smooth path used time:', time.time() - t)
    print('Smooth path from {} to {}'.format(len(path), len(sp)))

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
    width_c = 600
    height_c = 600
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
    btn_load_robot = QPushButton('Load robot')
    btn_load_robot.resize(100, 50)
    btn_load_robot.clicked.connect(lambda: load_robot())
    btn_load_robot.clicked.connect(lambda: draw_data(label, width_c, height_c, scale))
    btn_load_robot.clicked.connect(lambda: target_box_update(box_target, scene))
    btn_load_robot.clicked.connect(lambda: pfield_box_update(box_pfield, scene))
    btn_load_robot.show()

    btn_load_obstacle = QPushButton('Load obstacle')
    btn_load_obstacle.resize(100, 50)
    btn_load_obstacle.clicked.connect(lambda: load_obstacle())
    btn_load_obstacle.clicked.connect(lambda: draw_data(label, width_c, height_c, scale))
    btn_load_obstacle.show()

    btn_reset = QPushButton('Reset')
    btn_reset.resize(100, 50)
    btn_reset.clicked.connect(lambda: reset())
    btn_reset.clicked.connect(lambda: draw_data(label, width_c, height_c, scale))
    btn_reset.clicked.connect(lambda: target_box_update(box_target, scene))
    btn_reset.clicked.connect(lambda: pfield_box_update(box_pfield, scene))
    btn_reset.show()

    btn_get_path = QPushButton('Search path')
    btn_get_path.resize(100, 50)
    btn_get_path.clicked.connect(lambda: get_path())
    btn_get_path.show()

    btn_smooth = QPushButton('Smooth path')
    btn_smooth.resize(100, 50)
    btn_smooth.clicked.connect(lambda: path_smoothing())
    btn_smooth.show()

    btn_replay = QPushButton('Replay path')
    btn_replay.resize(100, 50)
    btn_replay.clicked.connect(lambda: show_path())
    btn_replay.show()

    #combobox
    box_target = QComboBox()
    box_target.resize(100, 50)
    box_target.activated.connect(lambda: target_box_changed(box_target))
    box_target.show()

    box_pfield = QComboBox()
    box_pfield.resize(100, 50)
    box_pfield.activated.connect(lambda: pfield_box_changed(box_pfield, label, scene, width_c, height_c))
    box_pfield.show()

    box_pfield_enhance = QComboBox()
    box_pfield_enhance.resize(100, 50)
    box_pfield_enhance.activated.connect(lambda: pfield_enhance_box_changed(box_pfield_enhance))
    box_pfield_enhance.addItem('Potential field enhance: On', QVariant(True))
    box_pfield_enhance.addItem('Potential field enhance: Off', QVariant(False))
    box_pfield_enhance.setCurrentIndex(1)
    box_pfield_enhance.show()

    box_pvalue_enhance = QComboBox()
    box_pvalue_enhance.resize(100, 50)
    box_pvalue_enhance.activated.connect(lambda: pvalue_enhance_box_changed(box_pvalue_enhance))
    box_pvalue_enhance.addItem('Potential value enhance: On', QVariant(True))
    box_pvalue_enhance.addItem('Potential value enhance: Off', QVariant(False))
    box_pvalue_enhance.show()


    #layout
    layout_btn_data = QHBoxLayout()
    layout_btn_data.addWidget(btn_load_robot)
    layout_btn_data.addWidget(btn_load_obstacle)
    layout_btn_data.addWidget(btn_reset)

    layout_btn_path = QHBoxLayout()
    layout_btn_path.addWidget(btn_get_path)
    layout_btn_path.addWidget(btn_smooth)
    layout_btn_path.addWidget(btn_replay)

    layout = QVBoxLayout()
    layout.addWidget(label)
    layout.addLayout(layout_btn_data)
    layout.addLayout(layout_btn_path)
    layout.addWidget(box_target)
    layout.addWidget(box_pfield)
    layout.addWidget(box_pfield_enhance)
    layout.addWidget(box_pvalue_enhance)

    widget.setLayout(layout)

    app.exec()
