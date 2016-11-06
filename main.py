import sys
from obj import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

items = []
robots = []
obstacles = []

def read_data():
    #robot.dat
    data = []
    with open('robot.dat', 'r')as fread:
        for line in fread:
            if not line.startswith('#'):
                data += line.split()

    robot_num = int(data.pop(0))
    global robots
    for _ in range(robot_num):
        robots.append(Robot(data))

    #obstacle.dat
    data = []
    with open('obstacle.dat', 'r')as fread:
        for line in fread:
            if not line.startswith('#'):
                data += line.split()

    obstacle_num = int(data.pop(0))
    global obstacles
    for _ in range(obstacle_num):
        obstacles.append(Obstacle(data))

    global items
    items = robots + obstacles

def draw(pixmap, label):
    painter = QPainter(pixmap)

    for x in items:
        if type(x) is Robot:
            painter.setPen(QPen(QColor(0, 255, 0), 1))
        elif type(x) is Obstacle:
            painter.setPen(QPen(QColor(255, 0, 0), 1))
        else:
            painter.setPen(QPen(QColor(0, 0, 255), 1))

        x.draw(painter)

    painter.end()
    label.setPixmap(pixmap)

class CustomLabel(QLabel):
    def __init__(self, parent=None, flags=Qt.WindowFlags()):
        super(CustomLabel, self).__init__(parent, flags)

    def mousePressEvent(self, event):
        mousemap = {1: 'Left', 2: 'Right'}
        print('Mouse {} press at ({}, {})'.format(mousemap[event.button()], event.x(), event.y()))

    def mouseMoveEvent(self, event):
        print('Mouse at ({}, {})'.format(event.x(), event.y()))

    def mouseReleaseEvent(self, event):
        mousemap = {1: 'Left', 2: 'Right'}
        print('Mouse {} release at ({}, {})'.format(mousemap[event.button()], event.x(), event.y()))

if __name__ == '__main__':
    app = QApplication(sys.argv)

    #main widget
    widget = QWidget()
    widget.resize(600, 400)
    widget.setWindowTitle('GRA')
    widget.show()

    #button
    btn_read = QPushButton('Read data')
    btn_read.resize(100, 50)
    btn_read.clicked.connect(read_data)
    btn_read.show()

    btn_draw = QPushButton('Draw data')
    btn_draw.resize(100, 50)
    btn_draw.clicked.connect(lambda: draw(pixmap, label))
    btn_draw.show()

    #pixmap
    pixmap = QPixmap(600, 400)

    label = CustomLabel()
    label.setPixmap(pixmap)

    #layout
    layout_btn = QHBoxLayout()
    layout_btn.addWidget(btn_read)
    layout_btn.addWidget(btn_draw)

    layout = QVBoxLayout()
    layout.addWidget(label)
    layout.addLayout(layout_btn)

    widget.setLayout(layout)

    app.exec()
