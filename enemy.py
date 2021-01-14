from func import *
from player import Bullet
from random import randrange


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color, way, groups):
        super().__init__(*groups)
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height))
        self.image.fill(color)

        self.mask = pygame.mask.from_surface(self.image)
        self.timer = 0

        self.shoot_sound = load_sound('pew.wav')

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
        player, bullets_group, all_sprites = args
        if self.is_move:
            self.move_road()
        else:
            self.start_move_to_point(self.way[self.current_way])
            self.current_way += 1
            if self.current_way == len(self.way):
                self.way.reverse()
                self.current_way = 1

        if not self.shoot_flag and self.timer == 0 :
            pygame.time.set_timer(ENEMY_SHOOT_EVENT, self.shoot_delay, True)
            self.timer = 1

        self.shoot(player, bullets_group, all_sprites)

        self.bullets_collide(bullets_group)
        if self.health <= 0:
            self.health = 50
            self.current_way = 0

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

    def move_line(self):
        self.x += self.direction[0] * self.vx
        self.y -= self.direction[1] * self.vy

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

    def shoot(self, player, bullets_group, all_sprites):
        if math.dist(self.rect.center, player.rect.center) <= self.view_radius and self.shoot_flag:
            self.timer = 0
            self.shoot_flag = False
            cos, sin = calculate_direction(*self.rect.center, *player.rect.center)
            shoot_x, shoot_y = 100 * cos, 100 * sin
            real_pos = (player.rect.x + randrange(-50, 51), player.rect.y + randrange(-50, 51))
            bullet = Bullet((self.rect.x + shoot_x, self.rect.y + shoot_y), real_pos,
                            (all_sprites, bullets_group))
            ADD_BULLETS.append(((self.rect.x + shoot_x, self.rect.y + shoot_y), real_pos))
            pygame.mixer.find_channel(True).play(self.shoot_sound)

    def bullets_collide(self, bullets_group):
        for bullet in bullets_group.sprites():
            if pygame.sprite.collide_mask(self, bullet):
                bullet.kill()
                self.health -= 10
