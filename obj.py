import math
import copy
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class Vec2:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def print(self):
        print('({}, {})'.format(self.x, self.y))

    def toQPointF(self):
        return QPointF(self.x, self.y)

    def __add__(self, other):
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vec2(self.x - other.x, self.y - other.y)

    def __str__(self):
        return '({}, {})'.format(self.x, self.y)

    @staticmethod
    def dot(a, b):
        return a.x * b.y - a.y * b.x

Point = Vec2
Vector = Vec2

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

    def configured(self, conf):
        def transform(p, conf):
            sin = math.sin(math.radians(conf[2]))
            cos = math.cos(math.radians(conf[2]))
            return Point(p.x*cos - p.y*sin + conf[0], p.x*sin + p.y*cos + conf[1])

        result = copy.deepcopy(self)
        for i in range(len(result.vertices)):
            result.vertices[i] = transform(self.vertices[i], conf)
        return result

    def draw(self, painter, conf, fill = False):
        poly = self.configured(conf).toQPolygonF()
        painter.drawPolygon(poly)
        if fill:
            brush = QBrush(painter.pen().color())
            path = QPainterPath()
            path.addPolygon(poly)
            painter.fillPath(path, brush)

    @staticmethod
    def collision(a, b):
        def side(origin, a, b):
            return math.copysign(1.0, Vec2.dot(a - origin, b - origin))

        def edge_collision(a0, a1, b0, b1):
            return side(a0, a1, b0) != side(a0, a1, b1) and side(b0, b1, a0) != side(b0, b1, a1)

        for i in range(len(a.vertices)):
            for j in range(len(b.vertices)):
                if edge_collision(a.vertices[i-1], a.vertices[i], b.vertices[j-1], b.vertices[j]):
                    return True
        return False

class Item:
    def __init__(self, data):
        #read polygons
        self.polygon_num = int(data.pop(0))
        self.polygons = []
        for _ in range(self.polygon_num):
            self.polygons.append(Polygon(data))

        #read init conf
        self.init_conf = [float(data.pop(0)), float(data.pop(0)), float(data.pop(0))]

        #set temp conf
        self.temp_conf = [0.0, 0.0, 0.0]

    def scale(self, scale):
        self.init_conf = [self.init_conf[0]*scale, self.init_conf[1]*scale, self.init_conf[2]]
        for poly in self.polygons:
            for v in poly.vertices:
                v.x *= scale
                v.y *= scale

    def conf(self):
        return [init+temp for init, temp in zip(self.init_conf, self.temp_conf)]

    def contains(self, x, y):
        for poly in self.polygons:
            if poly.configured(self.conf()).toQPolygonF().containsPoint(QPointF(x, y), Qt.WindingFill):
                return True
        else:
            return False

    def print(self):
        #print polygons
        for i in range(self.polygon_num):
            print('Polygon {}:'.format(i))
            self.polygons[i].print()

        #print init conf
        print('Init conf: {}'.format(self.init_conf))

    def draw(self, painter):
        for poly in self.polygons:
            poly.draw(painter, self.conf())

    @staticmethod
    def collision(a, b):
        for pa in a.polygons:
            for pb in b.polygons:
                if Polygon.collision(pa.configured(a.conf()), pb.configured(b.conf())):
                    return True
        return False

class Robot(Item):
    def __init__(self, data):
        super(Robot, self).__init__(data)
        self.type = ''

        #read goal conf
        self.goal_conf = [float(data.pop(0)), float(data.pop(0)), float(data.pop(0))]

        #read control points
        self.control_num = int(data.pop(0))
        self.controls = []
        for _ in range(self.control_num):
            self.controls.append(Point(float(data.pop(0)), float(data.pop(0))))

    def scale(self, scale):
        super(Robot, self).scale(scale)
        self.goal_vconf = [self.goal_conf[0]*scale, self.goal_conf[1]*scale, self.goal_conf[2]]

    def print(self):
        super().print()

        #print goal conf
        print('Goal conf: {}'.format(self.goal_conf))

        #print control points
        for i in range(self.control_num):
            print('Control point {}:'.format(i))
            self.controls[i].print()

class Obstacle(Item):
    def __init__(self, data):
        super(Obstacle, self).__init__(data)
