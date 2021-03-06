import pygame
import pygame_gui
import pyganim

WINDOW_SIZE = WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 720
FPS = 60
WALL_WIDTH = WALL_HEIGHT = TILE_WIDTH = TILE_HEIGHT = 32
WALL_COLOR = 'red'
LEVELS_DIR = 'levels'

# events
CAN_SHOOT_EVENT = pygame.USEREVENT + 3
ENEMY_SHOOT_EVENT = pygame.USEREVENT + 3
MYEVENTTYPE = pygame.USEREVENT + 1
ROUND_END = pygame.USEREVENT + 4
ROUND_DURATION_MIN = 5
ADD_BULLETS = []

# colors
BACKGROUND_COLOR = '#002137'

# NET
SERVER_IP = 'localhost'

# Map
WALLS_IDs = [1730, 1837, 1729, 2165, 2486, 2485, 2057, 1736, 1844, 2492]
SPAWN_IDs = [112]
LAMPS_IDs = [1599]

MOVE_SOUND = 0

anim_images = pyganim.getImagesFromSpriteSheet('data/anim.jpeg', rows=1, cols=6, rects=[])
