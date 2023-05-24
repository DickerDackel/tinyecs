import pygame
import tinyecs as ecs

import tinyecs.components as tec

from importlib.resources import files
from random import random, randint

from pygame.math import Vector2
from tinyecs.components import Comp

FPS = 60
SCREEN_WIDTH, SCREEN_HEIGHT = 1024, 768
BLACK = pygame.Color('black')

pygame.init()
pygame.display.set_caption('pygame minimal template')
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

image = pygame.image.load(
    files('demos.resources').joinpath('cursor.png')
).convert_alpha()

group = pygame.sprite.Group()


def create_thing():
    image = pygame.Surface((randint(5, 64), randint(5, 64)))
    image.fill(pygame.Color(randint(0, 255), randint(0, 255), randint(0, 255)))

    entity = ecs.create_entity()
    ecs.add_component(entity, Comp.SPRITE, tec.Sprite(image, group))
    ecs.add_component(entity, Comp.POSITION, tec.Position(Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))
    v = Vector2(random() * 150 + 150, 0)
    v.rotate_ip(random() * 360)
    ecs.add_component(entity, Comp.MOMENTUM, tec.Momentum(v))
    ecs.add_component(entity, Comp.CONTAINER, tec.Container(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))


ecs.add_system(tec.momentum_system, Comp.POSITION, Comp.MOMENTUM)
ecs.add_system(tec.sprite_system, Comp.SPRITE, Comp.POSITION)
ecs.add_system(tec.bounding_box_system, Comp.CONTAINER, Comp.SPRITE, Comp.POSITION, Comp.MOMENTUM)

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

    screen.fill(BLACK)

    group.update(dt)
    ecs.run_all_systems(dt)

    group.draw(screen)

    pygame.display.update()
    clock.tick(FPS)
    pygame.display.set_caption(f'FPS: {clock.get_fps():5.2f}, {len(group)} sprites')

pygame.quit()
