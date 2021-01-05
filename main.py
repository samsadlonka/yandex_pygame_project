import os
import sys
import math
from random import randrange

import pygame

pygame.init()

WINDOW_SIZE = WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 720
FPS = 60
WALL_WIDTH = WALL_HEIGHT = 32
WALL_COLOR = 'red'
LEVELS_DIR = 'levels'

CAN_SHOOT_EVENT = pygame.USEREVENT + 3
# KILL_PLAYER = pygame.USEREVENT + 4

all_sprites = pygame.sprite.Group()  # все объекты
bullets_group = pygame.sprite.Group()
entities = pygame.sprite.Group()  # пока тут только walls
enemies = pygame.sprite.Group()

screen = pygame.display.set_mode(WINDOW_SIZE)
clock = pygame.time.Clock()


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
    data = open(f"{LEVELS_DIR}/{filename}", 'rt').readlines()
    data = list(map(str.rstrip, data))
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


class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, groups):
        super().__init__(*groups)
        self.image = pygame.Surface((WALL_WIDTH, WALL_HEIGHT))
        self.image.fill(WALL_COLOR)
        self.rect = pygame.Rect(x, y, WALL_WIDTH, WALL_HEIGHT)


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, groups):
        super().__init__(*groups)

        self.vx = self.vy = 5
        self.speed = (0, 0)
        self.health = 100

        self.image_source = load_image('player.png')
        self.image_source = pygame.transform.rotate(self.image_source, 270)
        self.image = self.image_source.copy()
        self.angle = 0
        self.mask = pygame.mask.from_surface(self.image)

        self.shoot_sound = load_sound('pew.wav')

        self.rect = pygame.Rect(x, y + 20, self.image.get_width(), self.image.get_height())

        self.shoot_pos = (self.rect.x + 100, self.rect.y + 100)
        self.shoot_pos_now = None
        self.can_shoot_flag = True
        self.weapon_delay = 100

    def move(self):
        keys = pygame.key.get_pressed()
        self.speed = (0, 0)
        x_speed, y_speed = 0, 0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            x_speed += self.vx
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            x_speed -= self.vx
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            y_speed += self.vy
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            y_speed -= self.vy
        self.speed = (x_speed, y_speed)

        self.rect = self.rect.move(*self.speed)

    def update(self, *args, **kwargs):
        collide_group = args[0]

        mouse_btns, mouse_pos = args[1], args[2]
        camera = args[3]

        self.angle = find_angle(self.rect.centerx, self.rect.centery,
                                *camera.get_real_pos(mouse_pos))

        self.image, self.rect = rot_center(self.image_source, self.angle, *self.rect.center)

        self.shoot_pos = (self.rect.x + 110, self.rect.y + 60)
        self.shoot_pos_now = point_rot(self.shoot_pos, *self.rect.center, self.angle)
        self.mask = pygame.mask.from_surface(self.image)

        self.rotate_collide(collide_group)

        self.move()
        self.collide(collide_group)
        self.bullets_collide()

        if self.health <= 0:
            self.kill()

        if mouse_btns[0] and self.can_shoot_flag:
            pygame.time.set_timer(CAN_SHOOT_EVENT, self.weapon_delay, True)
            self.shoot(mouse_pos, camera)

    def bullets_collide(self):
        for bullet in bullets_group.sprites():
            if pygame.sprite.collide_mask(self, bullet):
                bullet.kill()
                self.health -= 10

    def rotate_collide(self, collide_group):
        for wall in collide_group:
            if self.rect.colliderect(wall.rect):
                e = [(10, 0), (-10, 0), (0, 10), (0, -10)]
                ans = (0, 0)
                for elem in e:
                    if not self.rect.move(*elem).colliderect(wall.rect):
                        ans = elem
                self.rect = self.rect.move(*ans)

    def collide(self, collide_group):  # коллизия собственного производства
        """Мы смотрим на предыдущий шаг,
        если смещение по х вызвало коллизию, то
        мы отменяем движение по х(как будто никто не двигался по х).
        Аналогично для y. Все это работает только тогда, когда есть коллизия"""
        collide_x = False
        collide_y = False
        collide = False
        without_x = self.rect.move(-self.speed[0], 0)
        without_y = self.rect.move(0, -self.speed[1])
        for wall in collide_group:

            if self.rect.colliderect(wall.rect):
                collide = True
                if without_x.colliderect(wall.rect):
                    collide_x = True
                if without_y.colliderect(wall.rect):
                    collide_y = True
        if collide:
            if not collide_x:
                self.rect = without_x
            if not collide_y:
                self.rect = without_y
            if collide_x and collide_y:
                self.rect = self.rect.move(-self.speed[0], -self.speed[1])

    def shoot(self, pos, camera):
        self.can_shoot_flag = False
        real_pos = camera.get_real_pos(pos)
        if pos[0] > self.rect.right or pos[0] < self.rect.left:
            bullet = Bullet(self.shoot_pos_now, real_pos, (bullets_group, all_sprites))
            self.shoot_sound.play()
        elif  pos[1] > self.rect.bottom or pos[1] < self.rect.top:
            bullet = Bullet(self.shoot_pos_now, real_pos, (bullets_group, all_sprites))
            self.shoot_sound.play()


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color, way, groups):
        super().__init__(*groups)
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height))
        self.image.fill(color)

        self.mask = pygame.mask.from_surface(self.image)

        self.x = x
        self.y = y
        self.width = width
        self.height = height

        self.end_x = self.end_y = self.direction = self.dist = None

        self.vx = self.vy = 4
        self.way = way
        self.current_way = 0
        self.is_move = False

        self.health = 50
        self.shoot_flag = True
        self.shoot_delay = 300
        self.last_shoot_time = None
        self.clock = pygame.time.Clock()
        self.view_radius = 100

    def update(self, *args, **kwargs):
        player = args[0]
        if self.is_move:
            self.move_road()
        else:
            self.start_move_to_point(self.way[self.current_way])
            self.current_way += 1
            self.current_way %= len(self.way)

        # self.shoot(player)  # fixit!!!!!!!!!

        if not self.shoot_flag:
            if self.clock.get_time() - self.last_shoot_time >= self.shoot_delay:
                self.shoot_flag = True

        self.bullets_collide()
        if self.health <= 0:
            self.kill()

    def start_move_to_point(self, coord):
        self.end_x = coord[0]
        self.end_y = coord[1]
        if self.x + self.width // 2 != self.end_x and self.y + self.height // 2 != self.end_y:
            self.is_move = True
            self.dist = ((self.end_x - (self.x + self.width // 2)) ** 2 + (
                    self.end_y - (self.x + self.width // 2)) ** 2) ** 0.5
            self.direction = ((self.end_x - (self.x + self.width // 2)) / self.dist,
                              (self.end_y - (self.x + self.width // 2)) / self.dist)

    def move_road(self):
        if self.end_x > self.x + self.width // 2:
            self.x += self.vx
        elif self.end_x < self.x + self.width // 2:
            self.x -= self.vx

        if self.end_y > self.y + self.height // 2:
            self.y += self.vy
        elif self.end_y < self.y + self.height // 2:
            self.y -= self.vy

        self.check_moving()

    def check_moving(self):
        if abs(self.x + self.width // 2 - self.end_x) < self.vx:
            self.x = self.end_x - self.width // 2
        if abs(self.y + self.height // 2 - self.end_y) < self.vy:
            self.y = self.end_y - self.height // 2

        if self.x == self.end_x - self.width // 2 and \
                self.y == self.end_y - self.height // 2:
            self.is_move = False
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def shoot(self, player):
        if math.dist(self.rect.center, player.rect.center) <= self.view_radius and self.shoot_flag:
            self.shoot_flag = False
            self.last_shoot_time = self.clock.get_time()
            print(self.last_shoot_time)
            cos, sin = calculate_direction(*self.rect.center, *player.rect.center)
            shoot_x, shoot_y = 100 * cos, 100 * sin
            bullet = Bullet((shoot_x, shoot_y),
                            (player.rect.x + randrange(-50, 51), player.rect.y + randrange(-50, 51)),
                            (all_sprites, bullets_group))

    def bullets_collide(self):
        for bullet in bullets_group.sprites():
            if pygame.sprite.collide_mask(self, bullet):
                bullet.kill()
                self.health -= 10


class Bullet(pygame.sprite.Sprite):
    def __init__(self, pos_start, pos_end, groups):
        super().__init__(*groups)
        self.image = pygame.Surface((20, 20))
        self.image.fill((250, 250, 0))
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.center = (pos_start[0], pos_start[1])
        self.speed = 1000 / FPS

        self.cos, self.sin = calculate_direction(*pos_start, *pos_end)

    def update(self):
        self.rect.x += self.cos * self.speed
        self.rect.y += self.sin * self.speed

        if pygame.sprite.spritecollide(self, entities, False):
            self.kill()


class Camera(object):
    def __init__(self, camera_func, width, height):
        self.camera_func = camera_func
        self.state = pygame.Rect(0, 0, width, height)

    def apply(self, target):
        return target.rect.move(self.state.topleft)

    def rect_apply(self, rect):
        return rect.move(self.state.topleft)

    def get_real_pos(self, pos):
        x, y = pos
        x -= self.state.x
        y -= self.state.y
        return (x, y)

    def update(self, target):
        self.state = self.camera_func(self.state, target.rect)


def camera_configure(camera, target_rect):
    l, t, _, _ = target_rect
    _, _, w, h = camera
    l, t = -l + WINDOW_WIDTH / 2, -t + WINDOW_HEIGHT / 2

    l = min(0, l)  # Не движемся дальше левой границы
    l = max(-(camera.width - WINDOW_WIDTH), l)  # Не движемся дальше правой границы
    t = max(-(camera.height - WINDOW_HEIGHT), t)  # Не движемся дальше нижней границы
    t = min(0, t)  # Не движемся дальше верхней границы

    return pygame.Rect(l, t, w, h)


def start_screen():
    intro_text = ["ЗАСТАВКА", "",
                  "Правила игры",
                  "Если в правилах несколько строк,",
                  "приходится выводить их построчно"]

    fon = pygame.surface.Surface(WINDOW_SIZE)
    fon.fill('blue')
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 30)
    text_coord = 50
    for line in intro_text:
        string_rendered = font.render(line, True, pygame.Color('black'))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top = text_coord
        intro_rect.x = 10
        text_coord += intro_rect.height
        screen.blit(string_rendered, intro_rect)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN or \
                    event.type == pygame.MOUSEBUTTONDOWN:
                return  # начинаем игру
        pygame.display.flip()
        clock.tick(FPS)


def main():
    level = load_level('test.txt')
    game_over_pic = load_image('game_over.png')
    game_over_pic = pygame.transform.scale(game_over_pic, WINDOW_SIZE)

    player = Player(100, 100, (all_sprites,))  # создаем игрока
    camera = Camera(camera_configure, len(level[0]) * WALL_WIDTH, len(level) * WALL_HEIGHT)  # создаем камеру
    enemy = Enemy(200, 200, 50, 50, 'red', [(300, 300), (900, 900)], (all_sprites, enemies))

    light = load_image('circle.png')
    light = pygame.transform.scale(light, (100, 100))

    # lamps_coord = []
    # for i in range(10):
    #     lamps_coord.append((50 * i, 100))

    for i in range(len(level)):
        for j in range(len(level[0])):
            if level[i][j] == '-':
                wl = Wall(j * WALL_WIDTH, i * WALL_HEIGHT, (all_sprites, entities))

    running = True
    game_over = False
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == CAN_SHOOT_EVENT:
                player.can_shoot_flag = True
            if game_over and event.type == pygame.KEYDOWN and \
                    event.key == pygame.K_SPACE:
                player = Player(100, 100, (all_sprites,))
                game_over = False

        # updates
        camera.update(player)

        player.update(entities, pygame.mouse.get_pressed(3), pygame.mouse.get_pos(), camera)
        bullets_group.update()
        enemies.update(player)

        # renders
        screen.fill((150, 150, 150))

        for e in all_sprites:
            screen.blit(e.image, camera.apply(e))

        # lightning
        screen_filter = pygame.surface.Surface(WINDOW_SIZE)
        screen_filter.fill((255, 255, 255))
        # pygame.draw.circle(screen_filter, ('black'), camera.apply(player).center, 300)
        for b in bullets_group:
            # pygame.draw.circle(screen_filter, 'black', camera.apply(b).center, 20)
            screen_filter.blit(light, list(map(lambda x: x - light.get_width() // 2, camera.apply(b).center)))
        # screen_filter.blit(light, list(map(lambda x: x - 3 * 50, pygame.mouse.get_pos())))
        # screen_filter.blit(light, list(map(lambda x: x - light.get_width() // 2, camera.apply(player).center)))
        pygame.draw.circle(screen_filter, 'black', camera.apply(player).center, 200)
        screen.blit(screen_filter, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

        for wl in entities:
            screen.blit(wl.image, camera.apply(wl))
        pygame.draw.rect(screen, 'yellow', camera.apply(player), 1)

        if player not in all_sprites.sprites():
            screen.fill('black')
            screen.blit(game_over_pic, (0, 0))

            game_over = True

        # flip
        pygame.display.flip()
        # clock
        clock.tick(FPS)


if __name__ == '__main__':
    # start_screen()
    main()
