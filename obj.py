from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def print(self):
        print('({}, {})'.format(self.x, self.y))

    def toQPointF(self):
        return QPointF(self.x, self.y)

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

    def toQPolygonF(self):
        return QPolygonF([v.toQPointF() for v in self.vertices])

    def draw(self, painter, conf, fill = False):
        trans = QTransform()
        trans.scale(4, 4)
        trans.translate(conf[0], conf[1])
        trans.rotate(conf[2])
        poly = trans.map(self.toQPolygonF())
        painter.drawPolygon(poly)
        if fill:
            brush = QBrush(painter.pen().color())
            path = QPainterPath()
            path.addPolygon(poly)
            painter.fillPath(path, brush)

class Item:
    def __init__(self, data):
        #read polygons
        self.polygon_num = int(data.pop(0))
        self.polygons = []
        for _ in range(self.polygon_num):
            self.polygons.append(Polygon(data))

        #read init conf
        self.init = [float(data.pop(0)), float(data.pop(0)), float(data.pop(0))]

    def print(self):
        #print polygons
        for i in range(self.polygon_num):
            print('Polygon {}:'.format(i))
            self.polygons[i].print()

        #print init conf
        print('Init conf: {}'.format(self.init))

    def draw(self, painter):
        for x in self.polygons:
            x.draw(painter, self.init)

class Robot(Item):
    def __init__(self, data):
        super(Robot, self).__init__(data)

        #read goal conf
        self.goal = [float(data.pop(0)), float(data.pop(0)), float(data.pop(0))]

        #read control points
        self.control_num = int(data.pop(0))
        self.controls = []
        for _ in range(self.control_num):
            self.controls.append(Point(float(data.pop(0)), float(data.pop(0))))

    def print(self):
        super().print()

        #print goal conf
        print('Goal conf: {}'.format(self.goal))

        #print control points
        for i in range(self.control_num):
            print('Control point {}:'.format(i))
            self.controls[i].print()

class Obstacle(Item):
    def __init__(self, data):
        super(Obstacle, self).__init__(data)
