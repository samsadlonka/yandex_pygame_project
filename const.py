import pygame
import pygame_gui

WINDOW_SIZE = WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 720
FPS = 60
WALL_WIDTH = WALL_HEIGHT = 32
WALL_COLOR = 'red'
LEVELS_DIR = 'levels'


# events
CAN_SHOOT_EVENT = pygame.USEREVENT + 3
ROUND_END = pygame.USEREVENT + 4
ROUND_DURATION_MIN = 5
ADD_BULLETS = []

# colors
BACKGROUND_COLOR = '#002137'


# NET
SERVER_IP = 'localhost'
client_ip = 'localhost'