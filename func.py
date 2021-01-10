import math
import os
import sys
import pytmx


from const import *


def find_angle(x1, y1, x2, y2):
    rad = math.atan2(-(y2 - y1), x2 - x1)
    degree = math.degrees(rad)
    return degree


def rot_center(image, angle, x, y):
    rotated_image = pygame.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(center=image.get_rect(center=(x, y)).center)

    return rotated_image, new_rect


def point_rot(point, x0, y0, alpha):
    x, y = point
    alpha = math.radians(alpha)
    new_x = (x - x0) * math.cos(alpha) - -(y - y0) * math.sin(alpha) + x0
    new_y = -(x - x0) * math.sin(alpha) + (y - y0) * math.cos(alpha) + y0

    return int(new_x), int(new_y)


def calculate_direction(x1, y1, x2, y2):
    distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    cos = (x2 - x1) / distance
    sin = (y2 - y1) / distance
    return cos, sin


def load_level(filename):
    data = pytmx.load_pygame(f"{'levels'}/{filename}")
    return data


def terminate():
    pygame.quit()
    sys.exit()


def load_sound(name):
    fullname = os.path.join('data', name)
    sound = pygame.mixer.Sound(fullname)
    return sound


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    # если файл не существует, то выходим
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)

    return image
