class WebContainer:
    def __init__(self, player_pos=(100, 100), player_angle=0, bullets=None, score=0, k_death=0, **kwargs):
        self.player_pos = player_pos
        self.player_angle = player_angle
        self.bullets = bullets
        self.score = score
        self.k_death = k_death
