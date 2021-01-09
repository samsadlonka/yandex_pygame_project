import datetime as dt
import random

from func import *
from network import Network
from player import Player, Bullet
from enemy import Enemy
from camera import Camera, camera_configure

pygame.init()

all_sprites = pygame.sprite.Group()  # все объекты
bullets_group = pygame.sprite.Group()
entities = pygame.sprite.Group()  # пока тут только walls
enemies = pygame.sprite.Group()
player2_group = pygame.sprite.Group()

screen = pygame.display.set_mode(WINDOW_SIZE)
clock = pygame.time.Clock()


class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, groups):
        super().__init__(*groups)
        self.image = pygame.Surface((WALL_WIDTH, WALL_HEIGHT))
        self.image.fill(WALL_COLOR)
        self.rect = pygame.Rect(x, y, WALL_WIDTH, WALL_HEIGHT)


class SpawnPoint(pygame.sprite.Sprite):
    def __init__(self, x, y, groups):
        super().__init__(*groups)
        self.image = pygame.Surface((WALL_WIDTH, WALL_HEIGHT))
        self.image.fill('green')
        self.rect = pygame.Rect(x, y, WALL_WIDTH, WALL_HEIGHT)


class Player2(pygame.sprite.Sprite):
    def __init__(self, groups):
        super().__init__(*groups)
        self.rect = pygame.Rect(0, 0, 100, 100)
        self.source_image = load_image('player.png')
        self.image = load_image('player.png')
        self.mask = pygame.mask.from_surface(self.image)

    def change_pos(self, pos):
        self.rect.topleft = pos

    def change_angle(self, angle):
        self.image, self.rect = rot_center(self.source_image, angle - 90, *self.rect.center)
        self.mask = pygame.mask.from_surface(self.image)


def start_screen():
    intro_text = ["Начать игру", "",
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


def show_restart_info(scr):
    fnt = pygame.font.Font(None, 50)
    text = fnt.render('Press "Space" to respawn', True, (100, 100, 255))
    scr.blit(text, (WINDOW_WIDTH // 2 - text.get_width() // 2, WINDOW_HEIGHT // 2 - text.get_height() // 2))


def show_player_hp(scr, player):
    fnt = pygame.font.Font(None, 50)
    text = fnt.render('HP: {}'.format(player.health), True, (255, 255, 255))
    pygame.draw.rect(scr, BACKGROUND_COLOR,
                     (0, WINDOW_HEIGHT - text.get_height() - 20, text.get_width() + 20, text.get_height() + 20))
    scr.blit(text, (10, WINDOW_HEIGHT - text.get_height() - 10))


def show_round_time(scr, round_start_time):
    secs = int((dt.datetime.now() - round_start_time).total_seconds())
    secs = 60 * ROUND_DURATION_MIN - secs
    time = dt.time(minute=secs // 60, second=secs % 60).strftime('%M:%S')

    fnt = pygame.font.Font(None, 50)
    text = fnt.render(time, True, (255, 255, 255))
    pygame.draw.rect(scr, BACKGROUND_COLOR,
                     (WINDOW_WIDTH - text.get_width() - 20, WINDOW_HEIGHT - text.get_height() - 20,
                      text.get_width() + 20, text.get_height() + 20))
    scr.blit(text, (WINDOW_WIDTH - text.get_width() - 10, WINDOW_HEIGHT - text.get_height() - 10))


def show_score(scr, player):
    fnt = pygame.font.Font(None, 50)
    text = fnt.render(f"You {player.score}:{player.k_death} Opponent", True, (255, 255, 255))
    pygame.draw.rect(scr, BACKGROUND_COLOR, (
        WINDOW_WIDTH // 2 - text.get_width() // 2 - 20, WINDOW_HEIGHT - text.get_height() - 20, text.get_width() + 20,
        text.get_height() + 20))

    scr.blit(text, (WINDOW_WIDTH // 2 - text.get_width() // 2 - 10, WINDOW_HEIGHT - text.get_height() - 10))


def show_escape_info(scr):
    fnt = pygame.font.Font(None, 50)
    text = fnt.render('Press "Esc" to back to menu', True, (100, 100, 255))
    scr.blit(text, (WINDOW_WIDTH // 2 - text.get_width() // 2, 500))


def main():
    level = load_level('normal map.txt')
    spawn_points = []
    game_over_pic = load_image('game_over.png')
    game_over_pic = pygame.transform.scale(game_over_pic, WINDOW_SIZE)

    # round timer
    pygame.time.set_timer(ROUND_END, ROUND_DURATION_MIN * 60 * 1000, True)
    start_time = dt.datetime.now()

    player = Player(100, 100, (all_sprites,))  # создаем игрока
    player2 = Player2((all_sprites, player2_group))
    camera = Camera(camera_configure, len(level[0]) * WALL_WIDTH, len(level) * WALL_HEIGHT)  # создаем камеру
    enemy = Enemy(200, 200, 50, 50, 'red', [(300, 300), (900, 900)], (all_sprites, enemies))

    """NETWORK"""
    n = Network()
    """DANGER!"""

    light = load_image('circle.png')
    light = pygame.transform.scale(light, (100, 100))

    # lamps_coord = []
    # for i in range(10):
    #     lamps_coord.append((50 * i, 100))

    for i in range(len(level)):
        for j in range(len(level[0])):
            if level[i][j] == '-':
                wl = Wall(j * WALL_WIDTH, i * WALL_HEIGHT, (all_sprites, entities))
            if level[i][j] == 'S':
                spawn_points.append((j * WALL_WIDTH, i * WALL_HEIGHT))
                sp_p = SpawnPoint(*spawn_points[-1], (all_sprites,))

    player.rect.topleft = random.choice(spawn_points)
    player.is_alive = False
    running = True
    game_over = False
    while running:

        """NETWORK!"""
        player2_pos, player2_angle, other_bullets_coords, player.score = n.send(player.rect.topleft, player.angle,
                                                                                ADD_BULLETS, player.k_death)
        player2.change_pos(player2_pos)
        player2.change_angle(player2_angle)
        for blt in other_bullets_coords:
            bullet = Bullet(*blt, (bullets_group, all_sprites))
            player.shoot_sound.play()
        ADD_BULLETS.clear()
        """DANGER!"""

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == CAN_SHOOT_EVENT:
                player.can_shoot_flag = True
            if not player.is_alive and event.type == pygame.KEYDOWN and \
                    event.key == pygame.K_SPACE:
                player.rect.topleft = random.choice(spawn_points)
                player.is_alive = True
                player.health = 100
            if event.type == ROUND_END:
                game_over = True
            if game_over and event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                # start_menu()
                return 0
        if not game_over:
            # updates
            camera.update(player)
            if player.is_alive:
                player.update(entities, pygame.mouse.get_pressed(3), pygame.mouse.get_pos(), camera, bullets_group,
                              all_sprites)
            enemies.update(player, bullets_group, all_sprites)
            bullets_group.update(entities, player2)

            # renders
            screen.fill((150, 150, 150))

            for e in all_sprites:
                screen.blit(e.image, camera.apply(e))
            screen.blit(player.image, camera.apply(player))

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

            show_player_hp(screen, player)
            show_round_time(screen, start_time)
            show_score(screen, player)

            if not player.is_alive:
                screen.fill('black')
                show_restart_info(screen)
        else:
            screen.blit(game_over_pic, (0, 0))
            show_score(screen, player)
            show_escape_info(screen)

        # flip
        pygame.display.flip()
        # clock
        clock.tick(FPS)


if __name__ == '__main__':
    # start_screen()

    # danger
    #   |
    #  \ /
    #   .
    from webContainer import WebContainer

    # ----not danger----

    main()
