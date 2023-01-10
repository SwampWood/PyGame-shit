import os
import sys

import pygame


pygame.init()
clock = pygame.time.Clock()
size = width, height = 1024, 600
screen = pygame.display.set_mode(size)
screen.fill(pygame.Color('blue'))
pygame.display.set_caption('Revenge is a dish best served sticky')
all_allies = pygame.sprite.Group()
all_enemies = pygame.sprite.Group()
all_objects = pygame.sprite.Group()


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


class Spider(pygame.sprite.Sprite):
    images_movement_right = [load_image("SpiderWalking1.png"), load_image("SpiderWalking2.png"),
                             load_image("SpiderWalking3.png"), load_image("SpiderWalking4.png")]

    images_movement_left = [pygame.transform.flip(i, True, False) for i in images_movement_right]

    def __init__(self):
        super().__init__(all_allies)
        self.current = 1
        self.wait = 10
        self.y_velocity = 0
        self.drop = False
        self.direction = True
        self.image = Spider.images_movement_right[self.current]
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.x = 50
        self.rect.y = 400

    def update(self, check):
        if check[pygame.K_d]:
            self.rect.x += 2
            self.direction = True
            if self.wait:
                self.wait -= 1
            else:
                self.wait = 10
                self.current = (self.current + 1) % 4
                print(1)
        elif check[pygame.K_a]:
            self.rect.x -= 2
            self.direction = False
            if self.wait:
                self.wait -= 1
            else:
                self.wait = 10
                self.current = (self.current + 1) % 4
        else:
            self.current = 1

        if check[pygame.K_SPACE]:
            if self.y_velocity == 0:
                self.y_velocity = -10
                self.drop = True
        if self.drop:
            self.rect.y += self.y_velocity
            self.y_velocity += 1
        if self.direction:
            self.image = Spider.images_movement_right[self.current]
        else:
            self.image = Spider.images_movement_left[self.current]


if __name__ == '__main__':
    background = load_image("background.png")
    player = Spider()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            '''if event.type == pygame.MOUSEBUTTONDOWN:
                Landing(event.pos)'''

        screen.blit(background, (0, 0))

        all_allies.draw(screen)
        all_allies.update(check=pygame.key.get_pressed())
        clock.tick(60)
        pygame.display.flip()
    pygame.quit()