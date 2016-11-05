import sys
from random import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def print(self):
        print('({}, {})'.format(self.x, self.y))

class Polygon:
    def __init__(self, data):
        self.vertex_num = int(data.pop(0))
        self.vertices = []
        for _ in range(self.vertex_num):
            self.vertices.append(Point(float(data.pop(0)), float(data.pop(0))))

    def print(self):
        for i in range(self.vertex_num):
            print('Vertex {}:'.format(i))
            self.vertices[i].print()

    def draw(self, painter, conf, fill = False):
        trans = QTransform()
        trans.scale(4, 4)
        trans.translate(conf[0], conf[1])
        trans.rotate(conf[2])
        poly = trans.map(QPolygonF([QPointF(v.x, v.y) for v in self.vertices]))
        painter.drawPolygon(poly)
        if fill:
            brush = QBrush(painter.pen().color())
            path = QPainterPath()
            path.addPolygon(poly)
            painter.fillPath(path, brush)

class Robot:
    def __init__(self, data):
        #read polygons
        self.polygon_num = int(data.pop(0))
        self.polygons = []
        for _ in range(self.polygon_num):
            self.polygons.append(Polygon(data))

        #read conf
        self.init = [float(data.pop(0)), float(data.pop(0)), float(data.pop(0))]
        self.goal = [float(data.pop(0)), float(data.pop(0)), float(data.pop(0))]

        #read control points
        self.control_num = int(data.pop(0))
        self.controls = []
        for _ in range(self.control_num):
            self.controls.append(Point(float(data.pop(0)), float(data.pop(0))))

    def print(self):
        for i in range(self.polygon_num):
            print('Polygon {}:'.format(i))
            self.polygons[i].print()

        print('Init conf: {}'.format(self.init))
        print('Goal conf: {}'.format(self.goal))

        for i in range(self.control_num):
            print('Control point {}:'.format(i))
            self.controls[i].print()

    def draw(self, painter):
        for x in self.polygons:
            x.draw(painter, self.init)

class Obstacle:
    def __init__(self, data):
        #read polygons
        self.polygon_num = int(data.pop(0))
        self.polygons = []
        for _ in range(self.polygon_num):
            self.polygons.append(Polygon(data))

        #read conf
        self.init = [float(data.pop(0)), float(data.pop(0)), float(data.pop(0))]

    def print(self):
        for i in range(self.polygon_num):
            print('Polygon {}:'.format(i))
            self.polygons[i].print()

        print('Init conf: {}'.format(self.init))

    def draw(self, painter):
        for x in self.polygons:
            x.draw(painter, self.init)

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
