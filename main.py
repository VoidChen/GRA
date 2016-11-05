import sys
from obj import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

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

def draw(pixmap, label):
    painter = QPainter(pixmap)

    painter.setPen(QPen(QColor(0, 255, 0), 1))
    for x in robots:
        x.draw(painter)

    painter.setPen(QPen(QColor(255, 0, 0), 1))
    for x in obstacles:
        x.draw(painter)

    painter.end()
    label.setPixmap(pixmap)

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

    label = QLabel()
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
