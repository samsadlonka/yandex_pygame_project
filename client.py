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

    running = True
    game_over = False
    while running:

        """NETWORK!"""
        player2_pos, player2_angle, other_bullets_coords = n.send(player.rect.topleft, player.angle, ADD_BULLETS)
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
            if game_over and event.type == pygame.KEYDOWN and \
                    event.key == pygame.K_SPACE:
                player = Player(100, 100, (all_sprites,))
                game_over = False

        # updates
        camera.update(player)

        player.update(entities, pygame.mouse.get_pressed(3), pygame.mouse.get_pos(), camera, bullets_group, all_sprites)
        enemies.update(player, bullets_group, all_sprites)
        bullets_group.update(entities, player2)

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

    # danger
    from webContainer import WebContainer

    # not danger

    main()
