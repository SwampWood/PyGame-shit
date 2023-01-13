import os
import sys
import random
import pygame


pygame.init()
clock = pygame.time.Clock()
size = width, height = 1024, 600
screen = pygame.display.set_mode(size)
screen.fill(pygame.Color('blue'))
pygame.display.set_caption('Revenge is a dish best served sticky')
all_sprites = pygame.sprite.Group()
all_enemies = pygame.sprite.Group()
all_allies = pygame.sprite.Group()
all_platforms = pygame.sprite.Group()
horizontal_borders = pygame.sprite.Group()


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


class Border(pygame.sprite.Sprite):
    # строго вертикальный отрезок
    def __init__(self, x1, y1, x2):
        super().__init__(horizontal_borders)
        self.image = pygame.Surface([x2 - x1, 1])
        self.rect = pygame.Rect(x1, y1, x2 - x1, 1)


class Particle(pygame.sprite.Sprite):
    # сгенерируем частицы разного размера
    fire = [load_image("particle.png")]
    for scale in (1, 2, 3):
        fire.append(pygame.transform.scale(fire[0], (scale, scale)))

    def __init__(self, pos, dx, dy):
        super().__init__(all_sprites)
        self.image = random.choice(self.fire)
        self.rect = self.image.get_rect()

        # у каждой частицы своя скорость — это вектор
        self.velocity = [dx, dy]
        # и свои координаты
        self.rect.x, self.rect.y = pos

        # гравитация будет одинаковой (значение константы)
        self.gravity = -0.5

    def update(self, check):
        # применяем гравитационный эффект:
        # движение с ускорением под действием гравитации
        self.velocity[1] += self.gravity
        if self.velocity[0]:
            self.velocity[0] += self.gravity * (self.velocity[0] // abs(self.velocity[0]))
        # перемещаем частицу
        self.rect.x += int(self.velocity[0])
        self.rect.y += int(self.velocity[1])
        # убиваем, если частица ушла за экран
        if self.velocity[1] >= 0 or self.velocity[0] == 0:
            self.kill()


class Spider(pygame.sprite.Sprite):
    images_movement_right = [load_image("SpiderWalking1.png"), load_image("SpiderWalking2.png"),
                             load_image("SpiderWalking3.png"), load_image("SpiderWalking4.png")]

    images_movement_left = [pygame.transform.flip(i, True, False) for i in images_movement_right]

    def __init__(self):
        super().__init__(all_sprites)
        self.add(all_allies)
        self.current = 1
        self.wait = 10
        self.x_velocity = 0
        self.y_velocity = 0
        self.drop = False
        self.direction = True
        self.image = Spider.images_movement_right[self.current]
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.x = 50
        self.rect.y = 400
        self.save_point = (50, 400)
        self.health = 1000
        self.current_sprite = None

    def respawn(self):
        if self.health == 1:
            '''EndScreen()'''
        else:
            self.health -= 1
            self.rect.x = self.save_point[0]
            self.rect.y = self.save_point[1]
            self.x_velocity = 0
            self.y_velocity = 0

    def update(self, check):
        if check[pygame.K_d]:
            if self.x_velocity < 0:
                self.x_velocity += 2
            self.x_velocity += 1
            self.direction = self.x_velocity >= 0
            if self.wait:
                self.wait -= 1
            else:
                self.wait = 10
                self.current = (self.current + 1) % 4
        elif check[pygame.K_a]:
            if self.x_velocity > 0:
                self.x_velocity -= 2
            self.x_velocity -= 1
            self.direction = self.x_velocity >= 0
            if self.wait:
                self.wait -= 1
            else:
                self.wait = 10
                self.current = (self.current + 1) % 4
        else:
            self.current = 1
            if self.x_velocity:
                self.x_velocity -= self.x_velocity // abs(self.x_velocity) * 2
                if self.x_velocity == 1:
                    self.x_velocity = 0

        if check[pygame.K_SPACE]:
            if self.y_velocity == 0 and not self.drop:
                self.current_sprite = None
                self.save_point = (self.rect.x - 10, self.rect.y - 100)
                self.y_velocity = -20
                self.rect.y -= 5
                if self.x_velocity >= 25:
                    self.x_velocity = 60
                elif self.x_velocity <= -25:
                    self.x_velocity = -60
                self.drop = True
        for i in all_platforms:
            if pygame.sprite.collide_mask(self, i):
                self.current_sprite = i
                self.y_velocity = 0
                self.rect.y -= 40
                if pygame.sprite.collide_mask(self, i):
                    self.x_velocity = -self.x_velocity // 3
                    self.rect.x += 15
                    if pygame.sprite.collide_mask(self, i):
                        self.rect.x -= 30
                    self.rect.y += 40
                else:
                    self.rect.y += 40
                    while pygame.sprite.collide_mask(self, i):
                        self.rect.y -= 1
                    else:
                        self.rect.y += 1
                    self.drop = False
                break
            else:
                self.drop = True
        if self.drop:
            if pygame.sprite.spritecollideany(self, horizontal_borders) and self.y_velocity <= 0 and self.rect.y < 5:
                self.y_velocity = -self.y_velocity // 2
            elif pygame.sprite.spritecollideany(self, horizontal_borders):
                self.respawn()
            self.rect.y += self.y_velocity
            self.y_velocity = min(50, self.y_velocity + 1)
        else:
            self.x_velocity = max(-30, min(30, self.x_velocity))
        self.rect.x += self.x_velocity // 5
        if self.direction:
            self.image = Spider.images_movement_right[self.current]
        else:
            self.image = Spider.images_movement_left[self.current]


class FlowerPlatform(pygame.sprite.Sprite):
    images = [load_image("Platforms1.png"), load_image("Platforms2.png"),
              load_image("Platforms1.png"), load_image("Platforms1.png")]

    def __init__(self, x, y, type_):
        super().__init__(all_sprites)
        self.add(all_platforms)
        self.image = FlowerPlatform.images[type_]
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.particles = False
        self.rect.x = x
        self.rect.y = y

    def update(self, check):
        if not self.particles and pygame.sprite.collide_mask(self, player) and player.current_sprite != self:
            for i in range(random.randint(60, 100)):
                Particle((self.rect.x + self.rect.width // 2, self.rect.y + self.rect.height // 8),
                         random.randint(-10, 10), random.randint(-2, 0))
            self.particles = True
        elif not pygame.sprite.collide_mask(self, player):
            self.particles = False


def create_map():
    # Здесь будем использовать различные классы для создания карты
    FlowerPlatform(20, 500, 1)
    FlowerPlatform(600, 300, 0)


background = load_image("background.png")
create_map()
player = Spider()
Border(0, -2, 1024)
Border(-200, 700, 1224)
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        '''if event.type == pygame.MOUSEBUTTONDOWN:
            Landing(event.pos)'''

    screen.blit(background, (0, 0))

    all_sprites.draw(screen)
    all_sprites.update(pygame.key.get_pressed())
    clock.tick(60)
    pygame.display.flip()
pygame.quit()
