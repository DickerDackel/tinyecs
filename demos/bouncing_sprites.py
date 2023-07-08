import pygame
import tinyecs as ecs

import tinyecs.components as ecsc

from importlib.resources import files
from random import random, randint

from pygame import Vector2

FPS = 60
SCREEN = pygame.Rect(0, 0, 1024, 768)

pygame.init()
pygame.display.set_caption('pygame minimal template')
screen = pygame.display.set_mode(SCREEN.size)
clock = pygame.time.Clock()


class Sprite(pygame.sprite.Sprite):
    def __init__(self, image, *groups):
        super().__init__(*groups)
        self.image = image
        self.rect = self.image.get_rect()


def bounding_box_system(dt, eid, world, position, momentum):
    if position.x < 0:
        position.x = -position.x
        momentum.x = -momentum.x
    elif position.x > world.width:
        position.x = 2 * world.width - position.x
        momentum.x = -momentum.x
    if position.y < 0:
        position.y = -position.y
        momentum.y = -momentum.y
    elif position.y > world.height:
        position.y = 2 * world.height - position.y
        momentum.y = -momentum.y


def create_thing():
    image = pygame.Surface((randint(5, 64), randint(5, 64)))
    image.fill(pygame.Color(randint(0, 255), randint(0, 255), randint(0, 255)))

    entity = ecs.create_entity()
    ecs.add_component(entity, 'sprite', Sprite(image, group))
    ecs.add_component(entity, 'position', Vector2(SCREEN.center))
    v = Vector2(random() * 150 + 150, 0)
    v.rotate_ip(random() * 360)
    ecs.add_component(entity, 'momentum', v)
    ecs.add_component(entity, 'container', SCREEN)


group = pygame.sprite.Group()


ecs.add_system(ecsc.momentum_system, 'momentum', 'position')
ecs.add_system(ecsc.sprite_system, 'sprite', 'position')
ecs.add_system(bounding_box_system, 'container', 'position', 'momentum')

for i in range(16):
    create_thing()

running = True
while running:
    dt = clock.get_time() / 1000.0

    for e in pygame.event.get():
        match e.type:
            case pygame.QUIT:
                running = False

            case pygame.KEYDOWN:
                match e.key:
                    case pygame.K_ESCAPE:
                        running = False
                    case pygame.K_SPACE:
                        for i in range(16):
                            create_thing()

    screen.fill('black')

    group.update(dt)
    ecs.run_all_systems(dt)

    group.draw(screen)

    pygame.display.update()
    clock.tick(FPS)
    pygame.display.set_caption(f'FPS: {clock.get_fps():5.2f}, {len(group)} sprites')

pygame.quit()
