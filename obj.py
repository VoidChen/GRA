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

    def transform(self, conf, scale = 1):
        sin = math.sin(math.radians(conf[2]))
        cos = math.cos(math.radians(conf[2]))
        return Point((self.x*cos - self.y*sin + conf[0]) * scale, (self.x*sin + self.y*cos + conf[1]) * scale)

    def y_convert(self, height):
        return Point(self.x, height - self.y)

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

    def configured(self, conf, scale = 1):
        result = copy.deepcopy(self)
        for i in range(len(result.vertices)):
            result.vertices[i] = self.vertices[i].transform(conf, scale)
        return result

    def y_convert(self, height):
        result = copy.deepcopy(self)
        for i in range(len(result.vertices)):
            result.vertices[i] = self.vertices[i].y_convert(height)
        return result

    def draw(self, painter, fill = True):
        poly = self.toQPolygonF()
        painter.drawPolygon(poly)
        if fill:
            brush = QBrush(painter.pen().color())
            path = QPainterPath()
            path.addPolygon(poly)
            painter.fillPath(path, brush)

    def draw_pfield(self, pfield):
        def scan(v1, v2):
            nonlocal x_min, x_max, y_min, y_max

            x_start = max(math.ceil(v1.x), 0)
            x_end = min(math.floor(v2.x), len(pfield)-1)

            if x_start < x_min or x_min is -1:
                x_min = math.floor(v1.x)
            if x_end > x_max or x_max is -1:
                x_max = math.ceil(v2.x)

            if v1.x != v2.x:
                dy = (v2.y - v1.y)/(v2.x - v1.x)
                for x in range(x_start, x_end+1):
                    y = (x-v1.x) * dy + v1.y
                    if y > y_max[x] or y_max[x] is -1:
                        y_max[x] = y
                    if y < y_min[x] or y_min[x] is -1:
                        y_min[x] = y
            else:
                x = min(x_start, len(pfield)-1)
                y = max(v1.y, v2.y)
                if y > y_max[x] or y_max[x] is -1:
                    y_max[x] = y
                y = min(v1.y, v2.y)
                if y < y_min[x] or y_min[x] is -1:
                    y_min[x] = y

        x_min = -1
        x_max = -1
        y_min = [-1 for _ in range(len(pfield))]
        y_max = [-1 for _ in range(len(pfield))]

        for i in range(len(self.vertices)):
            if self.vertices[i-1].x <= self.vertices[i].x:
                scan(self.vertices[i-1], self.vertices[i])
            else:
                scan(self.vertices[i], self.vertices[i-1])

        for i in range(x_min, min(x_max+1, len(pfield))):
            for j in range(max(math.floor(y_min[i]), 0), min(math.ceil(y_max[i])+1, len(pfield[0]))):
                pfield[i][j] = -2

    def contains(self, p):
        def side(origin, a, b):
            return math.copysign(1.0, Vec2.dot(a - origin, b - origin))

        sign = side(self.vertices[-1], self.vertices[0], p)
        for i in range(1, len(self.vertices)):
            if side(self.vertices[i-1], self.vertices[i], p) != sign:
                return False
        return True

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

        #set other attr
        self.temp_conf = [0.0, 0.0, 0.0]
        self.index = 0

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
            if poly.configured(self.conf()).contains(Point(x, y)):
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

    def draw(self, painter, height_c, scale):
        for poly in self.polygons:
            poly.configured(self.conf(), scale).y_convert(height_c).draw(painter)

    def draw_pfield(self, pfield, scale = 1):
        for poly in self.polygons:
            poly.configured(self.conf(), scale).draw_pfield(pfield)

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

class Scene:
    def __init__(self):
        self.robot_init = []
        self.robot_goal = []
        self.obstacle = []
        self.items = [self.robot_init, self.robot_goal, self.obstacle]
        self.robot_num = 0
        self.obstacle_num = 0
