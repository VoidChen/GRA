import time
from obj import *
from PyQt5.QtGui import *

def build_pfield(scene, rc, width, height, scale = 1, border_extend = 0):
    #init border
    border_extend = math.floor(scene.robot_goal[rc[0]].control_radius[rc[1]])

    #extend function
    neighbor = [[0, 1], [0, -1], [1, 0], [-1, 0]]
    def extend(x, y):
        for i in neighbor:
            nx = x+i[0]
            ny = y+i[1]
            if height > nx >= 0 and width > ny >= 0 and pfield[nx][ny] is -1:
                pfield[nx][ny] = pfield[x][y] + 1
                queue.append([nx, ny])
                nonlocal max_potential
                if pfield[nx][ny] > max_potential:
                    max_potential = pfield[nx][ny]

    t = time.time()

    #init pfield
    pfield = [[-1 for _ in range(height)] for _ in range(width)]

    #draw obstacle
    for obstacle in scene.obstacle:
        obstacle.draw_pfield(pfield, scale=scale, extend=border_extend)

    for robot in scene.robot_init:
        if robot.index != rc[0]:
            robot.draw_pfield(pfield, scale=scale, extend=border_extend)

    #set start
    start = scene.robot_goal[rc[0]].controls[rc[1]].transform(scene.robot_goal[rc[0]].conf(), scale)
    max_potential = 1
    pfield[int(start.x)][int(start.y)] = 0

    queue = []
    counter = 0
    queue.append([int(start.x), int(start.y)])
    while counter < len(queue):
        extend(*queue[counter])
        counter += 1

    for i in range(width):
        for j in range(height):
            if pfield[i][j] < 0:
                pfield[i][j] = max_potential * 1.5

    print('Build potential field used time:', time.time() - t)

    return pfield

def draw_pfield(label, pfield, width, height):
    height_c = label.height()
    width_c = label.width()

    max_potential = 1
    for i in range(width):
        for j in range(height):
            if pfield[i][j] > max_potential:
                max_potential = pfield[i][j]

    image = QImage(width, height, QImage.Format_RGB32)
    for i in range(width):
        for j in range(height):
            image.setPixelColor(i, j, QColor(*([255.0 * pfield[i][(j+1) * -1]/max_potential]*3)))

    label.clear()
    label.setPixmap(QPixmap(image))
