from func import *


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, groups):
        super().__init__(*groups)

        self.vx = self.vy = 5
        self.speed = (0, 0)
        self.health = 100
        self.is_alive = True

        self.image_source = load_image('player.png')
        self.image_source = pygame.transform.rotate(self.image_source, 270)
        self.image = self.image_source.copy()
        self.angle = 0
        self.mask = pygame.mask.from_surface(self.image)

        self.shoot_sound = load_sound('pew.wav')
        self.move_sound = MOVE_SOUND
        self.kill_sound = load_sound('kill.wav')

        self.rect = pygame.Rect(x, y + 20, self.image.get_width(), self.image.get_height())

        self.shoot_pos = (self.rect.x + 100, self.rect.y + 100)
        self.shoot_pos_now = None
        self.can_shoot_flag = True
        self.weapon_delay = 150

        self.k_death = 0
        self.score = 0

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
        if x_speed != 0 or y_speed != 0:
            self.move_sound = 1
        else:
            self.move_sound = 0


    def update(self, *args, **kwargs):
        collide_group = args[0]

        mouse_btns, mouse_pos = args[1], args[2]
        camera = args[3]

        bullets_group = args[4]
        all_sprites = args[5]

        self.angle = find_angle(self.rect.centerx, self.rect.centery,
                                *camera.get_real_pos(mouse_pos))

        self.image, self.rect = rot_center(self.image_source, self.angle, *self.rect.center)

        self.shoot_pos = (self.rect.x + 110, self.rect.y + 60)
        self.shoot_pos_now = point_rot(self.shoot_pos, *self.rect.center, self.angle)
        self.mask = pygame.mask.from_surface(self.image)

        self.rotate_collide(collide_group)

        self.move()
        self.collide(collide_group)
        self.bullets_collide(bullets_group)

        if self.health <= 0:
            self.kill()
            self.is_alive = False
            self.rect.topleft = (-500, -500)  # перемещаем игрока за экран
            self.k_death += 1
            pygame.mixer.find_channel(True).play(self.kill_sound)

        if mouse_btns[0] and self.can_shoot_flag:
            pygame.time.set_timer(CAN_SHOOT_EVENT, self.weapon_delay, True)
            self.shoot(mouse_pos, camera, bullets_group, all_sprites)

    def bullets_collide(self, bullets_group):
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

    def shoot(self, pos, camera, bullets_group, all_sprites):
        self.can_shoot_flag = False
        real_pos = camera.get_real_pos(pos)
        # для проверки нужна реальная позиция мыши(в координатах игры, а не окна)
        if real_pos[0] > self.rect.right or real_pos[0] < self.rect.left:
            bullet = Bullet(self.shoot_pos_now, real_pos, (bullets_group, all_sprites))
            ADD_BULLETS.append((self.shoot_pos_now, real_pos))

            pygame.mixer.find_channel(True).play(self.shoot_sound)
        elif real_pos[1] > self.rect.bottom or real_pos[1] < self.rect.top:
            bullet = Bullet(self.shoot_pos_now, real_pos, (bullets_group, all_sprites))
            ADD_BULLETS.append((self.shoot_pos_now, real_pos))

            pygame.mixer.find_channel(True).play(self.shoot_sound)


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

    def update(self, *args):
        entities, player2 = args
        self.rect.x += self.cos * self.speed
        self.rect.y += self.sin * self.speed

        if pygame.sprite.spritecollide(self, entities, False) or pygame.sprite.collide_mask(self, player2):
            self.kill()
