import math
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

    def length(self):
        return (self.x**2 + self.y**2)**0.5

    def __add__(self, other):
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        return Vec2(self.x * other, self.y * other)

    def __truediv__(self, other):
        return Vec2(self.x / other, self.y / other)

    def __str__(self):
        return '({}, {})'.format(self.x, self.y)

    @staticmethod
    def cross(a, b):
        return a.x * b.y - a.y * b.x

    @staticmethod
    def dot(a, b):
        return a.x * b.x + a.y * b.y

Point = Vec2
Vector = Vec2

class Polygon:
    def __init__(self):
        self.vertex_num = 0
        self.vertices = []

    def get_data(self, data):
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
        result = Polygon()
        result.vertex_num = self.vertex_num
        for v in self.vertices:
            result.vertices.append(v.transform(conf, scale))
        return result

    def y_convert(self, height):
        result = Polygon()
        result.vertex_num = self.vertex_num
        for v in self.vertices:
            result.vertices.append(v.y_convert(height))
        return result

    def draw(self, painter, fill = True):
        poly = self.toQPolygonF()
        painter.drawPolygon(poly)
        if fill:
            brush = QBrush(painter.pen().color())
            path = QPainterPath()
            path.addPolygon(poly)
            painter.fillPath(path, brush)

    def draw_pfield(self, pfield, border = 0):
        def extend_neighbor(n):
            base = []
            for i in range(1, n):
                base.append([i, n-i])

            result = [[0, n], [n, 0], [0, -n], [-n, 0]]
            for x in base:
                result.append(x)
                result.append([x[0], x[1] * -1])
                result.append([x[0] * -1, x[1]])
                result.append([x[0] * -1, x[1] * -1])

            return result

        def set_pfield(x, y):
            if x_max >= x >= 0 and y_max >= y >= 0:
                pfield[x][y] = -2

            for neighbor in en:
                nx, ny = x + neighbor[0], y + neighbor[1]
                if x_max >= nx >= 0 and y_max >= ny >= 0:
                    pfield[nx][ny] = -2

        def scan(v1, v2):
            if v1.x == v2.x or abs(v1.y - v2.y) > abs(v1.x - v2.x):
                if(v1.y > v2.y):
                    v1, v2 = v2, v1

                dx = (v2.x - v1.x)/(v2.y - v1.y)
                x = v1.x
                for y in range(round(v1.y), round(v2.y)+1):
                    set_pfield(round(x), round(y))
                    x += dx
            else:
                if(v1.x > v2.x):
                    v1, v2 = v2, v1

                dy = (v2.y - v1.y)/(v2.x - v1.x)
                y = v1.y
                for x in range(round(v1.x), round(v2.x)+1):
                    set_pfield(round(x), round(y))
                    y += dy

        x_max = len(pfield) - 1
        y_max = len(pfield[0]) - 1
        en = extend_neighbor(border)

        for i in range(self.vertex_num):
            if self.vertices[i-1].x <= self.vertices[i].x:
                scan(self.vertices[i-1], self.vertices[i])
            else:
                scan(self.vertices[i], self.vertices[i-1])

    def contains(self, p):
        def side(origin, a, b):
            return math.copysign(1.0, Vec2.cross(a - origin, b - origin))

        sign = side(self.vertices[-1], self.vertices[0], p)
        for i in range(1, self.vertex_num):
            if side(self.vertices[i-1], self.vertices[i], p) != sign:
                return False
        return True

    @staticmethod
    def collision(a, b):
        def side(origin, a, b):
            return math.copysign(1.0, Vec2.cross(a - origin, b - origin))

        def edge_collision(a0, a1, b0, b1):
            return side(a0, a1, b0) != side(a0, a1, b1) and side(b0, b1, a0) != side(b0, b1, a1)

        for i in range(a.vertex_num):
            for j in range(b.vertex_num):
                if edge_collision(a.vertices[i-1], a.vertices[i], b.vertices[j-1], b.vertices[j]):
                    return True
        return False

class Item:
    def __init__(self, data):
        #read polygons
        self.polygon_num = int(data.pop(0))
        self.polygons = []
        for _ in range(self.polygon_num):
            polygon = Polygon()
            polygon.get_data(data)
            self.polygons.append(polygon)

        #read init conf
        self.init_conf = [float(data.pop(0)), float(data.pop(0)), float(data.pop(0))]

        #calc radius
        self.radius = 0
        for poly in self.polygons:
            for v in poly.vertices:
                temp_radius = ((v.x**2) + (v.y**2))**0.5
                if temp_radius > self.radius:
                    self.radius = temp_radius

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

    def draw_pfield(self, pfield, scale = 1, border = 0):
        for poly in self.polygons:
            poly.configured(self.conf(), scale).draw_pfield(pfield, int(border * scale))

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

        #calc control point radius
        self.calc_control_point_radius()

    def calc_control_point_radius(self):
        def nearest(point, end_a, end_b):
            len_square = ((end_b - end_a).length())**2
            if len_square == 0:
                return (point - end_a).length()
            else:
                t = Vec2.dot(point - end_a, end_b - end_a) / len_square
                return (point - (end_a + (end_b - end_a) * max(min(t, 1), 0))).length()

        self.control_radius = [-1 for _ in range(self.control_num)]
        for poly in self.polygons:
            for i in range(poly.vertex_num):
                for j in range(self.control_num):
                    temp = nearest(self.controls[j], poly.vertices[i-1], poly.vertices[i])
                    if temp < self.control_radius[j] or self.control_radius[j] == -1: 
                        self.control_radius[j] = temp

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
