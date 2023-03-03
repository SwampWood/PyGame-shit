import os
import sys
import random
import pygame
from math import atan2, sin, cos, degrees, radians


pygame.init()
clock = pygame.time.Clock()
size = width, height = 1024, 600
screen = pygame.display.set_mode(size)
screen.fill(pygame.Color('black'))
pygame.display.set_caption('Revenge is a dish best served sticky')
all_sprites = pygame.sprite.Group()
all_enemies = pygame.sprite.Group()
all_allies = pygame.sprite.Group()
all_projectiles = pygame.sprite.Group()
all_platforms = pygame.sprite.Group()
all_branches = pygame.sprite.Group()
all_attacks = pygame.sprite.Group()
tree = pygame.sprite.Group()
system_bars = pygame.sprite.Group()
current_UI = pygame.sprite.Group()
horizontal_borders = pygame.sprite.Group()
vertical_border = 3 * width
fullscreen = False
is_paused = False
login = ''


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
    return pygame.transform.scale(image, (image.get_size()[0] * (new_width + 50) / width,
                                          image.get_size()[1] * (new_height + 100) / height))


def create_map():
    # Здесь откроем файл с картой и добавим все объекты
    with open('map.txt') as file:
        exec(file.read())


def clear_UI():
    global background, current_UI
    background = pygame.transform.scale(load_image("background.png"), (width, height))
    current_UI = pygame.sprite.Group()


def new_game():
    global all_sprites, all_enemies, all_allies, all_platforms, tree
    global system_bars, current_UI, horizontal_borders, player, score, background
    all_sprites = pygame.sprite.Group()
    all_enemies = pygame.sprite.Group()
    all_allies = pygame.sprite.Group()
    all_platforms = pygame.sprite.Group()
    tree = pygame.sprite.Group()
    system_bars = pygame.sprite.Group()
    horizontal_borders = pygame.sprite.Group()
    clear_UI()
    player = Spider()
    create_map()
    Border(0, -2, 6624)
    Border(0, 700, 6624)
    HealthBar()
    score = Score()
    Tutorial()


class Camera:
    # зададим начальный сдвиг камеры
    def __init__(self):
        self.dx = 0
        self.boss = False

    # сдвинуть объект obj на смещение камеры
    def apply(self, obj):
        obj.rect.x += self.dx
        if obj.__class__.__name__ == 'Web':
            obj.target = (obj.target[0] + self.dx, obj.target[1])
        if obj.__class__.__name__ == 'Wasp':
            obj.right_pos += self.dx
            obj.left_pos += self.dx
        if obj.__class__.__name__ == 'Dragonfly':
            obj.pos_args = [(x + self.dx, y, v) for x, y, v in obj.pos_args]
        if obj.__class__.__name__ == 'BossFirstPhase':
            obj.pos_args = [(x + self.dx, y, v) for x, y, v in obj.pos_args]

    # позиционировать камеру на объекте target
    def update(self, target):
        global vertical_border
        if not self.boss:
            self.dx = -(target.rect.x + target.rect.w // 2 - width // 2)
        else:
            self.dx = -(target.rect.x - width // 6)
        player.save_point[0] += self.dx
        vertical_border += self.dx

    def BossCamTurn(self):
        if self.boss:
            self.boss = False
        else:
            self.boss = True


class Border(pygame.sprite.Sprite):
    # строго вертикальный отрезок
    def __init__(self, x1, y1, x2):
        super().__init__(all_sprites, horizontal_borders)
        self.image = pygame.Surface([x2 - x1, 1])
        self.rect = pygame.Rect(x1, y1, x2 - x1, 1)


class Particle(pygame.sprite.Sprite):
    # сгенерируем частицы разного размера
    fire = [load_image("particle.png")]
    for scale in (1, 2, 3):
        fire.append(pygame.transform.scale(fire[0], (scale, scale)))

    def __init__(self, pos, dx, dy, gravity=-0.5):
        super().__init__(all_sprites)
        self.image = random.choice(self.fire)
        self.rect = self.image.get_rect()

        # у каждой частицы своя скорость — это вектор
        self.velocity = [dx, dy]
        # и свои координаты
        self.rect.x, self.rect.y = pos

        # гравитация будет одинаковой (значение константы) (нет)
        self.gravity = gravity

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


class StalactiteParticle(Particle):
    fire = [load_image('dirt.png')]

    def __init__(self, pos, dx, dy, gravity=0.5):
        super().__init__(pos, dx, dy, gravity)
        self.randomheight = random.randint(height // 48, height // 12)

    def update(self, check):
        self.velocity[1] += self.gravity
        # перемещаем частицу
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]
        # убиваем, если частица ушла за экран
        if self.rect.y > self.randomheight:
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

    def change_text(self, text):
        self.text.kill()
        text = Text(-50, -50, self.rect.height - 10, text)
        text.rect.x = self.rect.x + (self.rect.width - text.image.get_width()) // 2
        text.rect.y = self.rect.y
        self.text = text


class InputLogin(pygame.sprite.Sprite):
    def __init__(self, w_widget=300, h_widget=30, w_screen=width, h_screen=height):
        super().__init__(current_UI)
        left, top = (w_screen - w_widget) // 2, (h_screen - h_widget) // 2
        self.rect = pygame.Rect((left, top, w_widget, h_widget))
        self.image = pygame.Surface((w_widget, h_widget), pygame.SRCALPHA, 32)
        self.image.fill("grey")
        self.font_size = 25
        self.font = pygame.font.Font("data/ComicSansMSPixel.ttf", self.font_size)
        self.login = ''
        self.text = self.font.render(self.login, True, "black")
        self.limit = self.rect.w - self.font_size

    def update(self, event=None, **kwargs):  # type of event is pygame.KEYDOWN
        if not event:  # unicode, key, mod, scancode, window
            return
        if event.key == 8:  # backspace
            self.login = self.login[:-1]
        elif event.key == 32:
            if len(self.login):
                self.login += event.unicode
        elif event.key not in (9, ):
            self.login += event.unicode
        text = self.font.render(self.login, True, "black")
        if text.get_width() > self.limit:
            self.login = self.login[:-1]
            return
        self.text = text
        self.image.fill("grey")
        self.image.blit(self.text, (10, 5))


class Text(pygame.sprite.Sprite):
    def __init__(self, x, y, size_, text, color=(255, 255, 255)):
        super().__init__(current_UI)
        self.text = text
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


class Settings:
    def __init__(self, prev):
        global background, current_UI
        current_UI = pygame.sprite.Group()
        Text(400, 50, 50, 'Настройки')
        background = pygame.transform.scale(load_image("Death_background.png"), (width, height))
        self.changescreen = Button(270, 200, 50, 500, 'Оконный режим' if fullscreen else 'Полноэкранный режим',
                                   func_=lambda: Settings.fullscreen(self))
        Button(270, 300, 50, 500, 'Настройки')
        Button(270, 400, 50, 500, 'Назад', func_=lambda: prev())

    def fullscreen(self):
        global fullscreen
        if self.changescreen.text.text == 'Полноэкранный режим':
            self.changescreen.change_text('Оконный режим')
        else:
            self.changescreen.change_text('Полноэкранный режим')
        fullscreen = not fullscreen
        pygame.display.toggle_fullscreen()


class Pause:
    def __init__(self):
        global background
        clear_UI()
        Text(430, 50, 60, 'Пауза')
        background = gameplay_background
        Button(270, 200, 50, 500, 'Продолжить', func_=clear_UI)
        Button(270, 300, 50, 500, 'Настройки', func_=lambda: Settings(Pause))
        Button(270, 400, 50, 500, 'Выйти из игры', func_=sys.exit)


class Tutorial:
    def __init__(self):
        global background
        clear_UI()
        Text(10, 20, 25, 'Передвижение - A или D')
        Text(300, 20, 25, 'Прыжок - Пробел')
        Text(552, 20, 25, 'Выстрел ядом - ЛКМ')
        Text(818, 20, 25, 'Укус - E')
        Text(775, 60, 25, 'Укус имеет шанс')
        Text(760, 90, 25, 'восстановить 1 жизнь')
        Text(10, 330, 25, 'Выстрел паутиной - ПКМ')
        Text(350, 360, 22, 'Осторожно!')
        Text(310, 395, 22, 'Паутина растягивается.')
        Text(280, 430, 22, 'Успейте спрыгнуть использовав')
        Text(370, 455, 22, 'Пробел')
        Text(500, 330, 25, 'Побеждайте противников')
        Text(560, 360, 25, 'и повышайте счет')
        Text(780, 330, 25, 'Вы можете съесть мух')
        Text(790, 360, 25, 'чтобы восстановить')
        Text(840, 390, 25, 'здоровье')
        button = Button(0, 0, width, height, '', func_=clear_UI)
        button.image.set_alpha(0)
        background = pygame.transform.scale(load_image("Tutorial.png"), (width, height))


class StartScreen:
    def __init__(self):
        global background
        clear_UI()
        Text(400, 50, 50, 'PyGame-shit')
        Text(290, 100, 50, 'Отомсти за своего отца')
        background = pygame.transform.scale(load_image("Death_background.png"), (width, height))
        Button(270, 200, 50, 500, 'Новая игра', func_=new_game)
        Button(270, 300, 50, 500, 'Настройки', func_=lambda: Settings(StartScreen))
        Button(270, 400, 50, 500, 'Выйти из игры', func_=sys.exit)


class GetName:
    def __init__(self):
        global background
        clear_UI()
        self.running = True
        Text(400, 50, 50, 'Введите имя')
        self.input_name = InputLogin()
        background = pygame.transform.scale(load_image("Death_background.png"), (width, height))
        Button(270, 500, 50, 500, 'Продолжить', func_=self.set_name)
        self.run()

    def set_name(self):
        global login
        login = self.input_name.login
        self.running = False

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for sprite in current_UI:
                        if sprite.__class__.__name__ == 'Button' and sprite.rect.collidepoint(event.pos):
                            sprite()
                if event.type == pygame.KEYDOWN:
                    self.input_name.update(event=event)

            screen.blit(background, (0, 0))
            current_UI.draw(screen)
            clock.tick(60)
            pygame.display.flip()


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


class Web(pygame.sprite.Sprite):
    web = load_image('Web.png')

    def __init__(self, target):
        super().__init__(all_sprites)
        self.add(all_allies)
        self.length = 13
        self.wait = 5
        # зададим угол, под которым находится цель
        self.angle = degrees(atan2((player.rect.y - target[1]), (target[0] - player.rect.x - 20))) + 270
        if target[0] - 512 < 0:
            self.x_negative = -1
        else:
            self.x_negative = 1
        if target[1] > player.rect.y + 25:
            self.y_negative = -1
        else:
            self.y_negative = 1
        self.image = pygame.transform.rotate(Web.web.subsurface(0, 0, 40, self.length + 5), self.angle)
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.x = player.rect.x + 15
        self.rect.y = player.rect.y + 30
        self.target = target

    def update(self, check):
        if not player.webbed:
            for x in all_branches:
                if pygame.sprite.collide_mask(self, x):
                    player.webbed = True
                    if player.x_velocity < 0:
                        self.target = (self.rect.x, self.rect.y)
                        player.going_up = True
                    else:
                        self.target = (self.rect.x + self.length * cos(radians(self.angle - 270)), self.rect.y)
                        player.going_up = False

            else:
                if self.length > 358:
                    player.web = None
                    self.kill()
                else:
                    self.angle = degrees(atan2((player.rect.y + 50 - self.target[1]),
                                               (self.target[0] - player.rect.x - 20))) + 270
                    self.image = pygame.transform.rotate(Web.web.subsurface(0, 0, 40, self.length), self.angle)
                    self.length += 15

                    self.mask = pygame.mask.from_surface(self.image)
                    self.rect.x = player.rect.x + 15
                    self.rect.y = player.rect.y + 30
                    if self.target[0] - 512 < 0:
                        self.rect.x -= sin(radians(self.angle)) * self.length
                    if self.y_negative == 1:
                        self.rect.y -= cos(radians(self.angle)) * self.length
        else:
            self.angle = degrees(atan2((player.rect.y + 50 - self.target[1]), (self.target[0] - 512))) + 270
            self.length = int(((self.target[0] - player.rect.x + 15) ** 2 + (player.rect.y - self.target[1] + 50) ** 2)
                              ** 0.5)
            self.image = pygame.transform.rotate(Web.web.subsurface(0, 0, 40, self.length), self.angle)
            self.mask = pygame.mask.from_surface(self.image)
            self.rect.x = player.rect.x + 15
            self.rect.y = self.target[1]
            if self.target[0] - 512 < 0:
                self.rect.x -= sin(radians(self.angle)) * self.length


class Bite(pygame.sprite.Sprite):
    bite = load_image('Bite.png')

    def __init__(self):
        super().__init__(all_sprites)
        self.add(all_attacks)
        self.damage = 110
        self.wait = 2
        self.frames = []
        self.cut_sheet(Bite.bite, 11)
        self.cur_frame = 0
        self.image = pygame.transform.flip(self.frames[self.cur_frame], not player.direction, False)
        self.mask = pygame.mask.from_surface(self.image)
        if player.direction:
            self.rect.x, self.rect.y = player.rect.x + 80, player.rect.y - 10
        else:
            self.rect.x, self.rect.y = player.rect.x - 30, player.rect.y - 10

    def cut_sheet(self, sheet, columns):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height())
        for i in range(columns):
            frame_location = (self.rect.w * i, 0)
            self.frames.append(sheet.subsurface(pygame.Rect(frame_location, self.rect.size)))

    def update(self, check):
        self.wait -= 1
        if self.wait == 0:
            self.cur_frame = (self.cur_frame + 1)
            if self.cur_frame == 11:
                self.kill()
            else:
                self.image = pygame.transform.flip(self.frames[self.cur_frame], not player.direction, False)
                self.mask = pygame.mask.from_surface(self.image)
                if player.direction:
                    self.rect.x, self.rect.y = player.rect.x + 80, player.rect.y - 10
                else:
                    self.rect.x, self.rect.y = player.rect.x - 30, player.rect.y - 10
                self.wait = 2


class Poison(pygame.sprite.Sprite):
    poison = load_image('Poison.png')

    def __init__(self, target):
        super().__init__(all_sprites)
        self.add(all_attacks)
        self.damage = 20
        self.wait = 6
        self.frames = []
        self.cut_sheet(Poison.poison, 4)
        self.cur_frame = 0
        self.angle = degrees(atan2((player.rect.y - target[1]), (target[0] - player.rect.x - 20)))
        self.x_velocity = int(cos(radians(self.angle)) * 20)

        self.y_velocity = -int(sin(radians(self.angle)) * 20)
        self.image = pygame.transform.rotate(self.frames[self.cur_frame], self.angle)
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.x, self.rect.y = player.rect.x + 30, player.rect.y

    def cut_sheet(self, sheet, columns):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height())
        for i in range(columns):
            frame_location = (self.rect.w * i, 0)
            self.frames.append(sheet.subsurface(pygame.Rect(frame_location, self.rect.size)))

    def update(self, check):
        self.wait -= 1
        if self.wait == 0:
            self.wait = 6
            self.cur_frame = (self.cur_frame + 1) % 4
        for i in all_platforms:
            if pygame.sprite.collide_mask(self, i):
                self.kill()
        for i in all_enemies:
            if pygame.sprite.collide_mask(self, i):
                self.kill()
        if pygame.sprite.spritecollideany(self, horizontal_borders) or pygame.sprite.spritecollideany(self, tree):
            self.kill()
        self.image = pygame.transform.rotate(self.frames[self.cur_frame], self.angle)
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.x += self.x_velocity
        self.rect.y += self.y_velocity


class Stalactite(pygame.sprite.Sprite):
    stalactite = pygame.transform.scale(load_image('Stalactite.png'), (20, 60))

    def __init__(self):
        super().__init__(all_sprites)
        self.add(all_projectiles)
        self.damage = 50
        self.image = Stalactite.stalactite
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.rect = self.rect.move(random.randint(0, width), -60)
        self.gravity = 5
        self.wait = 40

    def update(self, check):
        if self.wait:
            StalactiteParticle((self.rect.x, 0), random.randint(-1, 1), random.randint(0, 1), gravity=0.5)
            self.wait -= 1
        else:
            self.rect = self.rect.move(0, self.gravity)
            for i in all_enemies:
                if pygame.sprite.collide_mask(self, i):
                    i.health -= self.damage
                    i.immunity_frames = 60
                    self.kill()
            for attack in all_attacks:
                if pygame.sprite.collide_mask(self, attack):
                    self.kill()
                    attack.kill()


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
        self.going_up = False
        self.immunity_frames = 0
        self.attack_cd = 0
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
        self.webbed = False
        self.web = None

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
            if self.web:
                self.webbed = False
                self.web.kill()
                self.web = None

    def update(self, check):
        self.immunity_frames = max(0, self.immunity_frames - 1)
        self.attack_cd = max(0, self.attack_cd - 1)
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
            if self.x_velocity and not self.webbed:
                self.x_velocity -= self.x_velocity // abs(self.x_velocity) * 2
                if self.x_velocity == 1:
                    self.x_velocity = 0

        if check[pygame.K_SPACE]:

            if self.webbed and self.web:
                self.x_velocity = -50
                self.y_velocity = -20
                if self.web.target[0] - 512 < 0:
                    self.x_velocity = 50

            if self.web:
                self.web.kill()
                self.web = None

            self.webbed = False

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
                    if enemy.__class__.__name__ == "Fly":
                        self.health += 1
                        enemy.kill()
                    else:
                        self.respawn()
        if pygame.sprite.spritecollideany(self, all_projectiles) and not self.immunity_frames:
            for i in all_projectiles:
                if pygame.sprite.collide_mask(self, i):
                    self.respawn()
                    i.kill()
        if pygame.sprite.spritecollideany(self, horizontal_borders) and self.rect.y < 5:
            self.y_velocity = abs(self.y_velocity) // 2
            self.going_up = False
        elif pygame.sprite.spritecollideany(self, horizontal_borders):
            self.respawn()
        if self.webbed and self.web:
            velocity = (abs(2 * self.web.length * sin(radians(self.web.angle - 270)))) ** 0.5
            if self.going_up:
                velocity *= -1
            self.y_velocity = int(cos(radians(self.web.angle - 270)) * velocity)
            self.x_velocity = int(sin(radians(self.web.angle - 270)) * velocity)
            if self.web.angle >= 445 or self.web.angle <= 275:
                self.going_up = not self.going_up
                self.y_velocity = 10

        elif self.drop:
            self.y_velocity = min(50, self.y_velocity + 1)
        else:
            self.x_velocity = max(-30, min(30, self.x_velocity))
            self.save_point = [self.rect.x, self.rect.y - 20]
        if self.direction:
            self.image = Spider.images_movement_right[self.current]
        else:
            self.image = Spider.images_movement_left[self.current]
        self.rect.x += int(self.x_velocity) // 5
        self.rect.y += int(self.y_velocity)


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


class RockWall(pygame.sprite.Sprite):
    image = load_image("Cave_wall.png")

    def __init__(self, x, y):
        super().__init__(all_sprites)
        self.image = RockWall.image
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.particles = False
        self.rect.x = x
        self.rect.y = y


class RockPlatform(pygame.sprite.Sprite):
    image = load_image("Rock_Platform1.png")
    landing = pygame.mixer.Sound(os.path.join('data', 'music', f'rock_landing.mp3'))

    def __init__(self, x, y):
        super().__init__(all_sprites)
        self.add(all_platforms)
        self.image = RockPlatform.image
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.particles = False
        self.rect.x = x
        self.rect.y = y

    def update(self, check):
        if not self.particles and pygame.sprite.collide_mask(self, player) and player.current_sprite != self:
            self.particles = True
            RockPlatform.landing.set_volume(0.4)
            RockPlatform.landing.play(0)
        elif not pygame.sprite.collide_mask(self, player):
            self.particles = False


class FlowerPlatform(pygame.sprite.Sprite):
    images = [load_image("Platforms1.png"), load_image("Platforms2.png"),
              load_image("Platforms3.png"), load_image("Platforms1.png")]
    landing = pygame.mixer.Sound(os.path.join('data', 'music', f'grass_landing{random.randint(1, 3)}.mp3'))

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
            FlowerPlatform.landing.set_volume(0.05)
            FlowerPlatform.landing.play(0)
        elif not pygame.sprite.collide_mask(self, player):
            self.particles = False


class TreeBranch(pygame.sprite.Sprite):
    images = [load_image("Branch1.png"), load_image("Branch2.png"), load_image("Branch3.png")]

    def __init__(self, x, y, type_):
        super().__init__(all_sprites)
        self.add(all_branches)
        self.image = TreeBranch.images[type_]
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.particles = False
        self.rect.x = x
        self.rect.y = y


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, sheet, count, health=100):
        super().__init__(all_sprites)
        self.add(all_enemies)
        self.health = health
        self.poison_damage = 0
        self.wait = 5
        self.wait_max = 5
        self.frames = []
        self.cut_sheet(sheet, count)
        self.cur_frame = 0
        self.rotation = False
        self.image = self.frames[self.cur_frame]
        self.rect = self.rect.move(x, y)
        self.sound = None
        self.immunity_frames = 0
        self.cost = 50  # сколько очков добавляем за убийство

    def cut_sheet(self, sheet, columns):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height())
        for i in range(columns):
            frame_location = (self.rect.w * i, 0)
            self.frames.append(sheet.subsurface(pygame.Rect(frame_location, self.rect.size)))

    def update(self, check):
        self.wait -= 1
        self.immunity_frames = max(0, self.immunity_frames - 1)

        self.health -= 1 if self.poison_damage else 0
        self.poison_damage = max(0, self.poison_damage - 1)

        if self.wait == 0:
            self.cur_frame = (self.cur_frame + 1) % len(self.frames)
            self.image = pygame.transform.flip(self.frames[self.cur_frame], self.rotation, False)
            self.wait = self.wait_max
        if not self.immunity_frames:
            for i in all_attacks:
                if pygame.sprite.collide_mask(self, i):
                    self.health -= i.damage
                    self.immunity_frames = 60

                    if i.__class__.__name__ == 'Bite' and random.randint(1, 100) >= 90:
                        player.health += 1
                    elif i.__class__.__name__ == 'Poison':
                        self.poison_damage = 40

        if self.health <= 0:
            if self.sound:
                self.sound.fadeout(500)
            self.kill()
            score.score += self.cost


class Wasp(Enemy):
    enemy = load_image("Wasp.png")
    buzz = pygame.mixer.Sound(os.path.join('data', 'music', f'bee_sound.mp3'))

    def __init__(self, x, y, left_pos, right_pos, sheet=None, count=4, v=3, health=150):
        sheet = Wasp.enemy if not sheet else sheet
        super().__init__(x, y, sheet, count, health)
        self.left_pos = left_pos
        self.right_pos = right_pos
        self.v = v
        self.sound = Wasp.buzz
        self.sound.set_volume(0)
        self.sound.play(-1)
        self.cost = 150

    def update(self, check):
        super().update(check)
        if self.rotation:
            self.rect.x -= self.v  # v в пикселях
        else:
            self.rect.x += self.v  # v в пикселях
        if self.rect.x >= self.right_pos:
            self.rotation = True
        elif self.rect.x <= self.left_pos:
            self.rotation = False
        if abs(self.rect.x - player.rect.x) < 500:
            self.sound.set_volume(0.5 - abs(self.rect.x - player.rect.x) / 1000)
        else:
            self.sound.set_volume(0)


class Dragonfly(Enemy):
    enemy = load_image("Dragonfly.png")
    buzz = pygame.mixer.Sound(os.path.join('data', 'music', f'dragonfly_sound.mp3'))

    def __init__(self, x, y, pos_args, sheet=None, count=6, health=120, sleep=50):
        sheet = Dragonfly.enemy if not sheet else sheet
        super().__init__(x, y, sheet, count, health)
        self.pos_args = pos_args  # список корежей с координатами и скоростями
        self.wait = 3
        self.wait_max = 3
        self.sleep = sleep
        self.i = 0
        self.v = self.pos_args[self.i][2]
        self.sound = Dragonfly.buzz
        self.sound.set_volume(0)
        self.sound.play(-1)
        self.cost = 200

    def update(self, check):
        super().update(check)
        if self.sleep:
            self.sleep -= 1
        else:
            if self.v:
                self.rect.x += (self.pos_args[self.i][0] - self.rect.x) // self.v
                self.rect.y += (self.pos_args[self.i][1] - self.rect.y) // self.v
                self.v -= 1
            else:
                self.rect.x, self.rect.y = self.pos_args[self.i][:2]
                self.i = (self.i + 1) % len(self.pos_args)
                self.v = self.pos_args[self.i][2]
                self.sleep = 50
            if self.rect.x >= self.pos_args[self.i][0]:
                self.rotation = False
            elif self.rect.x <= self.pos_args[self.i][0]:
                self.rotation = True
        if abs(self.rect.x - player.rect.x) < 500:
            self.sound.set_volume(0.5 - abs(self.rect.x - player.rect.x) / 1000)
        else:
            self.sound.set_volume(0)


class Fly(Enemy):
    enemy = load_image("Black_Fly.png")

    def __init__(self, x, y, sheet=None, count=2, health=1):
        sheet = Fly.enemy if not sheet else sheet
        super().__init__(x, y, sheet, count, health)
        self.cost = 100


class BossFirstPhase(Enemy):
    enemy = pygame.transform.scale(load_image("SpiderIdleFront2.png"), (80, 80))
    buzz = pygame.mixer.Sound(os.path.join('data', 'music', f'boss_walking.mp3'))

    def __init__(self, x, y, pos_args, sheet=None, count=1, health=2000, sleep=50):
        sheet = BossFirstPhase.enemy if not sheet else sheet
        super().__init__(x, y, sheet, count, health)
        self.pos_args = pos_args  # список кортежей с координатами и скоростями
        self.wait = 3
        self.wait_max = 3
        self.sleep = sleep
        self.i = 0
        self.v = self.pos_args[self.i][2]
        self.sound = Dragonfly.buzz
        self.sound.set_volume(0)
        self.sound.play(-1)
        self.cost = 1000

    def update(self, check):
        super().update(check)
        if self.sleep:
            self.sleep -= 1
        else:
            if self.v:
                self.rect.x += (self.pos_args[self.i][0] - self.rect.x) // self.v
                self.rect.y += (self.pos_args[self.i][1] - self.rect.y) // self.v
                self.v -= 1
            else:
                self.rect.x, self.rect.y = self.pos_args[self.i][:2]
                self.i = (self.i + random.randint(1, 5)) % len(self.pos_args)
                self.v = self.pos_args[self.i][2]
                self.sleep = 50
            if abs(self.rect.x - player.rect.x) < 500:
                self.sound.set_volume(0.5 - abs(self.rect.x - player.rect.x) / 1000)
            else:
                self.sound.set_volume(0)


background = pygame.transform.scale(load_image("background.png"), (width, height))
player = Spider()
score = Score()
camera = Camera()
GetName()
StartScreen()
sound = pygame.mixer.Sound(os.path.join('data', 'music', 'background_music.mp3'))
sound.set_volume(0.03)
sound.play(-1)

running = True
count = 0
while running:
    if not current_UI:
        for event in pygame.event.get():
            keys = pygame.key.get_pressed()
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                is_paused = True
                Pause()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and not player.webbed and player.web is None:
                player.web = Web(pygame.mouse.get_pos())
                web_sound = pygame.mixer.Sound(os.path.join('data', 'music', 'web_soundeffect.mp3'))
                web_sound.set_volume(0.03)
                web_sound.play(0)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_e and not player.attack_cd:
                player.attack_cd = 30
                bite_sound = pygame.mixer.Sound(os.path.join('data', 'music',
                                                               f'bite_soundeffect{random.randint(1, 2)}.mp3'))
                bite_sound.set_volume(0.2)
                bite_sound.play(0)
                Bite()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not player.attack_cd:
                player.attack_cd = 30
                poison_sound = pygame.mixer.Sound(os.path.join('data', 'music', 'poison_soundeffect.mp3'))
                poison_sound.set_volume(0.2)
                poison_sound.play(0)
                Poison(event.pos)
            if keys[pygame.K_b] and event.type == pygame.KEYDOWN:
                camera.BossCamTurn()

        screen.blit(background, (0, 0))
        all_sprites.draw(screen)
        system_bars.draw(screen)
        score.update()
        all_sprites.update(pygame.key.get_pressed())
        system_bars.update()
        camera.update(player)
        for sprite in all_sprites:
            camera.apply(sprite)
        gameplay_background = screen.copy()

    else:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                for sprite in current_UI:
                    if sprite.__class__.__name__ == 'Button' and sprite.rect.collidepoint(event.pos):
                        sprite()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and is_paused:
                is_paused = False
                clear_UI()

        screen.blit(background, (0, 0))

        current_UI.update()
        current_UI.draw(screen)
    clock.tick(60)
    pygame.display.flip()
pygame.quit()
