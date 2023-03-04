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
tree = pygame.sprite.Group()
system_bars = pygame.sprite.Group()
current_UI = pygame.sprite.Group()
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


def create_map():
    # Здесь откроем файл с картой и добавим все объекты
    with open('map.txt') as file:
        exec(file.read())


def new_game():
    global all_sprites, all_enemies, all_allies, all_platforms, tree
    global system_bars, current_UI, horizontal_borders, player, score, background
    all_sprites = pygame.sprite.Group()
    all_enemies = pygame.sprite.Group()
    all_allies = pygame.sprite.Group()
    all_platforms = pygame.sprite.Group()
    tree = pygame.sprite.Group()
    system_bars = pygame.sprite.Group()
    current_UI = pygame.sprite.Group()
    horizontal_borders = pygame.sprite.Group()
    background = pygame.transform.scale(load_image("background.png"), (width, height))
    player = Spider()
    create_map()
    Border(0, -2, 6624)
    Border(0, 700, 6624)
    HealthBar()
    score = Score()


class Camera:
    # зададим начальный сдвиг камеры
    def __init__(self):
        self.dx = 0

    # сдвинуть объект obj на смещение камеры
    def apply(self, obj):
        obj.rect.x += self.dx

    # позиционировать камеру на объекте target
    def update(self, target):
        self.dx = -(target.rect.x + target.rect.w // 2 - width // 2)
        player.save_point[0] += self.dx


class Border(pygame.sprite.Sprite):
    # строго вертикальный отрезок
    def __init__(self, x1, y1, x2):
        super().__init__(all_sprites)
        self.add(horizontal_borders)
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


class Numbers(pygame.sprite.Sprite):
    numbers = [load_image(str(i) + '.png') for i in range(10)]

    def __init__(self, pos, num):
        super().__init__(system_bars)
        self.image = Numbers.numbers[int(num)]
        self.rect = self.image.get_rect()
        self.rect.x = 90 + pos * 50
        self.rect.y = 20


class Score:
    def __init__(self):
        self.score = 1000
        self.wait = 60
        self.numbers = [Numbers(i + 12, str(self.score).zfill(6)[i]) for i in range(6)]

    def __iadd__(self, other):
        self.score += other
        return self

    def update(self):
        for i in self.numbers:
            i.kill()
        self.wait -= 1
        if self.wait == 0:
            self.score = max(0, self.score - 1)
            self.wait = 60
        if self.score < 999999:
            self.numbers = [Numbers(i + 12, str(self.score).zfill(6)[i]) for i in range(6)]
        else:
            self.numbers = [Numbers(i + 12, '9') for i in range(6)]


class Button(pygame.sprite.Sprite):
    image = load_image("Button.png")

    def __init__(self, x, y, height_, width_, text, func_=None):
        super().__init__(current_UI)
        text = Text(-50, -50, height_ - 10, text)
        text.rect.x = x + (width_ - text.image.get_width()) // 2
        text.rect.y = y
        self.text = text
        self.image = pygame.transform.scale(Button.image, (width_, height_))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.func = func_

    def __call__(self):
        if self.func:
            self.func()


class Text(pygame.sprite.Sprite):
    def __init__(self, x, y, size_, text, color=(255, 255, 255)):
        super().__init__(current_UI)
        self.image = pygame.font.Font("data/ComicSansMSPixel.ttf", size_).render(text, True, color)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class EndScreen:
    def __init__(self):
        global background
        background = pygame.transform.scale(load_image("Death_background.png"), (width, height))
        Text(496 - 25 * len(str(score.score)), 50, 150, str(score.score))
        Text(20, 250, 50, 'Вы погибли и не смогли отомстить за своего отца...')
        Button(6, 500, 50, 500, 'Новая игра', func_=new_game)
        Button(518, 500, 50, 500, 'Выйти из игры', func_=sys.exit)


class StartScreen:
    def __init__(self):
        global background
        Text(400, 50, 50, 'Web-enge')
        Text(290, 100, 50, 'Отомсти за своего отца')
        background = pygame.transform.scale(load_image("Death_background.png"), (width, height))
        Button(270, 200, 50, 500, 'Новая игра', func_=new_game)
        Button(270, 300, 50, 500, 'Настройки')
        Button(270, 400, 50, 500, 'Выйти из игры', func_=sys.exit)


class HealthBar(pygame.sprite.Sprite):
    image = load_image("Heart.png")

    def __init__(self):
        super().__init__(system_bars)
        self.health = str(player.health) if player.health < 1000 else '999'
        self.numbers = [Numbers(i, self.health[i]) for i in range(len(self.health))]
        self.image = HealthBar.image
        self.rect = self.image.get_rect()
        self.rect.x = 20
        self.rect.y = 20

    def update(self):
        if str(player.health) != self.health:
            self.health = str(player.health) if player.health < 1000 else '999'
            for i in self.numbers:
                i.kill()
            self.numbers = [Numbers(i, self.health[i]) for i in range(len(self.health))]


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
        self.immunity_frames = 0
        self.drop = False
        self.direction = True
        self.image = Spider.images_movement_right[self.current]
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.x = 50
        self.rect.y = 400
        self.save_point = [50, 400]
        self.health = 10
        self.current_sprite = None

    def respawn(self):
        if self.health == 1:
            EndScreen()
        else:
            self.immunity_frames = 60
            self.health -= 1
            self.rect.x = self.save_point[0]
            self.rect.y = self.save_point[1]
            self.x_velocity = 0
            self.y_velocity = 0

    def update(self, check):
        self.immunity_frames = max(0, self.immunity_frames - 1)
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
        if pygame.sprite.collide_mask(self, [x for x in tree][0]):
            self.x_velocity = 60
        if pygame.sprite.spritecollideany(self, all_enemies) and not self.immunity_frames:
            for enemy in all_enemies:
                if pygame.sprite.collide_mask(self, enemy):
                    self.respawn()
        if pygame.sprite.spritecollideany(self, horizontal_borders) and self.y_velocity <= 0 and self.rect.y < 5:
            self.y_velocity = -self.y_velocity // 2
        elif pygame.sprite.spritecollideany(self, horizontal_borders):
            self.respawn()
        if self.drop:
            self.rect.y += self.y_velocity
            self.y_velocity = min(50, self.y_velocity + 1)
        else:
            self.x_velocity = max(-30, min(30, self.x_velocity))
            self.save_point = [self.rect.x, self.rect.y - 20]
        self.rect.x += self.x_velocity // 5
        if self.direction:
            self.image = Spider.images_movement_right[self.current]
        else:
            self.image = Spider.images_movement_left[self.current]


class TreeBorder(pygame.sprite.Sprite):
    images = load_image("TreeWall.png")

    def __init__(self):
        super().__init__(all_sprites)
        self.add(tree)
        self.image = TreeBorder.images
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.particles = False
        self.rect.x = -1000
        self.rect.y = -100


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


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, sheet, count, health=50):
        super().__init__(all_sprites)
        self.add(all_enemies)
        self.health = health
        self.wait = 5
        self.frames = []
        self.cut_sheet(sheet, count)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.rect.move(x, y)

    def cut_sheet(self, sheet, columns):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height())
        for i in range(columns):
            frame_location = (self.rect.w * i, 0)
            self.frames.append(sheet.subsurface(pygame.Rect(frame_location, self.rect.size)))

    def update(self, check):
        self.wait -= 1
        if self.wait == 0:
            self.cur_frame = (self.cur_frame + 1) % len(self.frames)
            self.image = self.frames[self.cur_frame]
            self.wait = 5


background = pygame.transform.scale(load_image("background.png"), (width, height))
player = Spider()
score = Score()
camera = Camera()
StartScreen()

running = True
while running:
    if not current_UI:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                player.respawn()

        screen.blit(background, (0, 0))
        all_sprites.draw(screen)
        system_bars.draw(screen)
        score.update()
        all_sprites.update(pygame.key.get_pressed())
        system_bars.update()

        camera.update(player)
        for sprite in all_sprites:
            camera.apply(sprite)
        clock.tick(60)

    else:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                for sprite in current_UI:
                    if sprite.__class__.__name__ == 'Button' and sprite.rect.collidepoint(event.pos):
                        sprite()
                        '''for j in current_UI:
                            j.kill()
                        current_UI = pygame.sprite.Group()'''

        screen.blit(background, (0, 0))

        current_UI.update()
        current_UI.draw(screen)

    pygame.display.flip()
pygame.quit()
