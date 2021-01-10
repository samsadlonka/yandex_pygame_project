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
pygame.time.set_timer(MYEVENTTYPE, 180)


class Wall(pygame.sprite.Sprite):
    def __init__(self, image, x, y, groups):
        super().__init__(*groups)
        self.image = image
        self.rect = pygame.Rect(x, y, TILE_WIDTH, TILE_HEIGHT)


class SpawnPoint(pygame.sprite.Sprite):
    def __init__(self, image, x, y, groups):
        super().__init__(*groups)
        self.image = image
        self.rect = pygame.Rect(x, y, TILE_WIDTH, TILE_HEIGHT)


class Player2(pygame.sprite.Sprite):
    def __init__(self, groups):
        super().__init__(*groups)
        self.rect = pygame.Rect(0, 0, 100, 100)
        self.source_image = load_image('player2.png')
        self.image = load_image('player2.png')
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
    if round_start_time:
        secs = int((dt.datetime.now() - round_start_time).total_seconds())
        secs = 60 * ROUND_DURATION_MIN - secs
        time = dt.time(minute=secs // 60, second=secs % 60).strftime('%M:%S')
    else:
        time = 'Waiting for player'

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


def show_info_player_disconnect(scr):
    fnt = pygame.font.Font(None, 50)
    text = fnt.render('Opponent is disconnected :(', True, (255, 255, 255))
    scr.blit(text, (WINDOW_WIDTH // 2 - text.get_width() // 2, 600))


def close_game():
    global all_sprites, bullets_group, entities, enemies, player2_group
    all_sprites = pygame.sprite.Group()  # все объекты
    bullets_group = pygame.sprite.Group()
    entities = pygame.sprite.Group()  # пока тут только walls
    enemies = pygame.sprite.Group()
    player2_group = pygame.sprite.Group()


def main(level_map):
    """NETWORK"""
    n = Network()

    p = n.getP()
    if p == 0:
        n.set_level(level_map)
    elif p == 1:
        level_map = n.get_level()

    """DANGER!"""

    level = load_level(level_map)
    spawn_points = []
    game_over_pic = load_image('game_over.png')
    game_over_pic = pygame.transform.scale(game_over_pic, WINDOW_SIZE)

    # round timer
    start_time = None

    player = Player(100, 100, (all_sprites,))  # создаем игрока
    player2 = Player2((all_sprites, player2_group))
    camera = Camera(camera_configure, level.width * WALL_WIDTH, level.height * WALL_HEIGHT)  # создаем камеру

    light = load_image('circle.png')
    light = pygame.transform.scale(light, (400, 400))

    lamps_coord = [(500, 500), (2000, 1000)]  # сделлать загрузку из map

    for i in range(level.height):
        for j in range(level.width):
            image = level.get_tile_image(j, i, 0)
            # screen.blit(image, (j * level.tilewidth, i * level.tilewidth))
            if get_tile_id(level, (j, i, 0)) in WALLS_IDs:
                wl = Wall(image, j * WALL_WIDTH, i * WALL_HEIGHT, (all_sprites, entities))
            if get_tile_id(level, (j, i, 0)) in SPAWN_IDs:
                spawn_points.append((j * WALL_WIDTH, i * WALL_HEIGHT))
                sp_p = SpawnPoint(image, *spawn_points[-1], (all_sprites,))

    player.rect.topleft = random.choice(spawn_points)
    player.is_alive = False
    running = True
    game_over = False
    flag_show_player_disconnect = False
    flag_player2_dead = True
    while running:
        prev_p_score = player.score
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

        if player.score != prev_p_score:
            flag_player2_dead = True

        if start_time is None and player2_pos[0] >= 0 and player2_pos[1] >= 0:
            start_time = dt.datetime.now()
            pygame.time.set_timer(ROUND_END, ROUND_DURATION_MIN * 60 * 1000, True)
            flag_player2_dead = False
            enemy = Enemy(200, 200, 50, 50, 'red', [(300, 300), (900, 900)], (all_sprites, enemies))
        elif not flag_player2_dead and start_time and player2_pos[0] < 0 and player2_pos[1] < 0:
            game_over = True
            flag_show_player_disconnect = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == CAN_SHOOT_EVENT:
                player.can_shoot_flag = True
            if event.type == MYEVENTTYPE and player.move_sound == 1:
                pygame.mixer.find_channel(True).play(load_sound('move_sound.wav'))
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
                pygame.draw.circle(screen_filter, 'black', camera.apply(b).center, 14)
                # screen_filter.blit(light, list(map(lambda x: x - light.get_width() // 2, camera.apply(b).center)))
            """Попытка сделать четверть окружности для поля зрения игрока"""
            # screen_filter.blit(light, list(map(lambda x: x - 3 * 50, pygame.mouse.get_pos())))
            # screen_filter.blit(light, list(map(lambda x: x - light.get_width() // 2, camera.apply(player).center)))
            # player_view = pygame.Surface((200, 200))
            # player_view.fill('white')
            # pygame.draw.circle(player_view, 'black', (0, 0), 200, 0, False, False, False, True)
            # player_view, rec = rot_center(player_view, player.angle, 0, 0)
            # screen_filter.blit(player_view, (100, 100))
            '''провал'''

            pygame.draw.circle(screen_filter, 'black', camera.apply(player).center, 100)

            # lamps
            for lmp_crd in lamps_coord:
                pygame.draw.circle(screen_filter, pygame.color.Color(0, 0, 0),
                                   camera.rect_apply(pygame.Rect(*lmp_crd, 1, 1)).center, 200, 0)

            screen.blit(screen_filter, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

            for wl in entities:
                screen.blit(wl.image, camera.apply(wl))
            # pygame.draw.rect(screen, 'yellow', camera.apply(player), 1)

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
            if flag_show_player_disconnect:
                show_info_player_disconnect(screen)

        # flip
        pygame.display.flip()
        # clock
        clock.tick(FPS)


def menu():
    global client_ip
    pygame.init()

    pygame.display.set_caption('menu')

    manager = pygame_gui.UIManager(WINDOW_SIZE)

    switch = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect(WINDOW_WIDTH // 2 - 200, 650, 400, 50),
        text='Start Game',
        manager=manager,
    )
    level = 'easy map.tmx'
    diff = pygame_gui.elements.ui_drop_down_menu.UIDropDownMenu(
        options_list=['Easy', 'Hard'],
        starting_option='Easy',
        relative_rect=pygame.Rect(WINDOW_WIDTH // 2 - 200, 250, 400, 50),
        manager=manager
    )
    entry = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect(WINDOW_WIDTH // 2 - 200, 500, 400, 100),
                                                manager=manager)
    entry.set_text('localhost')

    fnt = pygame.font.Font(None, 50)
    g_m = fnt.render('Game Menu', True, (255, 255, 255))
    mp = fnt.render('Map:', True, (255, 255, 255))
    ip = fnt.render('IP:', True, (255, 255, 255))
    wrong_ip = fnt.render('Wrong IP', True, (255, 0, 0))

    wrong_ip_flag = False

    clock_1 = pygame.time.Clock()
    run = True
    while run:
        time_delta = clock_1.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                confirmation_dialog = pygame_gui.windows.UIConfirmationDialog(
                    rect=pygame.Rect(WINDOW_WIDTH // 2 - 150, WINDOW_HEIGHT // 2 - 100, 300, 200),
                    manager=manager,
                    window_title='Exit Game',
                    action_long_desc='Are you sure?',
                    action_short_name='OK',
                    blocking=True
                )
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED:
                    run = False

                if event.user_type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
                    if event.text == 'Easy':
                        level = 'easy map.tmx'
                    elif event.text == 'Hard':
                        level = 'normal map.tmx'

                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == switch:
                        client_ip = entry.text
                        wrong_ip_flag = False
                        try:
                            main(level)
                            close_game()
                        except ConnectionError:
                            wrong_ip_flag = True
            manager.process_events(event)
        manager.update(time_delta)

        screen.fill('black')
        manager.draw_ui(screen)

        screen.blit(g_m, (WINDOW_WIDTH // 2 - g_m.get_width() // 2, 10))
        screen.blit(mp, (300, 250))
        screen.blit(ip, (300, 500))
        if wrong_ip_flag:
            screen.blit(wrong_ip, (900, 500))

        pygame.display.update()


if __name__ == '__main__':
    # start_screen()

    # danger
    #   |
    #  \ /
    #   .
    from webContainer import WebContainer

    # ----not danger----

    menu()
