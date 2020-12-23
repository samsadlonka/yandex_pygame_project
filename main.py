import pygame

WINDOW_SIZE = WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 720
FPS = 60
WALL_WIDTH = WALL_HEIGHT = 32
WALL_COLOR = 'red'
LEVELS_DIR = 'levels'

CAN_SHOOT_EVENT = pygame.USEREVENT + 3

all_sprites = pygame.sprite.Group()  # все объекты
bullets_group = pygame.sprite.Group()
entities = pygame.sprite.Group()  # пока тут только walls


class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, groups):
        super().__init__(*groups)
        self.image = pygame.Surface((WALL_WIDTH, WALL_HEIGHT))
        self.image.fill(WALL_COLOR)
        self.rect = pygame.Rect(x, y, WALL_WIDTH, WALL_HEIGHT)


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color, groups):
        super().__init__(*groups)

        self.rect = pygame.Rect(x, y, width, height)
        self.vx = self.vy = 5
        self.speed = (0, 0)

        self.image = pygame.Surface((width, height))
        self.image.fill(color)

        self.can_shoot_flag = True
        self.weapon_delay = 200


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

        self.move()
        self.collide(collide_group)
        if mouse_btns[0] and self.can_shoot_flag:
            pygame.time.set_timer(CAN_SHOOT_EVENT, self.weapon_delay, True)
            self.shoot(mouse_pos, camera)

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
        bullet = Bullet(self.rect.center, real_pos, (bullets_group, all_sprites))


class Bullet(pygame.sprite.Sprite):
    def __init__(self, pos_start, pos_end, groups):
        super().__init__(*groups)
        self.image = pygame.Surface((20, 20))
        self.image.fill((250, 250, 0))
        self.rect = self.image.get_rect()
        self.rect.center = (pos_start[0], pos_start[1])
        self.speed = 1000 / FPS

        self.cos, self.sin = self.calculate_direction(*pos_start, *pos_end)

    def update(self):
        self.rect.x += self.cos * self.speed
        self.rect.y += self.sin * self.speed

        if pygame.sprite.spritecollide(self, entities, False):
            self.kill()

    def calculate_direction(self, x1, y1, x2, y2):
        distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        cos = (x2 - x1) / distance
        sin = (y2 - y1) / distance
        return cos, sin


class Camera(object):
    def __init__(self, camera_func, width, height):
        self.camera_func = camera_func
        self.state = pygame.Rect(0, 0, width, height)

    def apply(self, target):
        return target.rect.move(self.state.topleft)

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


def load_level(filename):
    data = open(f"{LEVELS_DIR}/{filename}", 'rt').readlines()
    data = list(map(str.rstrip, data))
    return data


def main():
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE)

    level = load_level('test.txt')

    player = Player(100, 100, 50, 50, 'green', (all_sprites,))  # создаем игрока
    camera = Camera(camera_configure, len(level[0]) * WALL_WIDTH, len(level) * WALL_HEIGHT)  # создаем камеру

    for i in range(len(level)):
        for j in range(len(level[0])):
            if level[i][j] == '-':
                wl = Wall(j * WALL_WIDTH, i * WALL_HEIGHT, (all_sprites, entities))

    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == CAN_SHOOT_EVENT:
                player.can_shoot_flag = True
        # updates
        camera.update(player)

        player.update(entities, pygame.mouse.get_pressed(3), pygame.mouse.get_pos(), camera)
        bullets_group.update()

        # renders
        screen.fill('black')

        for e in all_sprites:
            screen.blit(e.image, camera.apply(e))

        # flip
        pygame.display.flip()
        # clock
        clock.tick(FPS)


if __name__ == '__main__':
    main()
