class WebContainer:
    def __init__(self, player_pos=(100, 100), player_angle=0, bullets=None, **kwargs):
        self.player_pos = player_pos
        self.player_angle = player_angle
        self.bullets = bullets
