import pygame
import tinyecs as ecs

import tinyecs.components as ecsc

from importlib.resources import files
from pygame.math import Vector2
from tinyecs.components import Comp

FPS = 60
SCREEN_WIDTH, SCREEN_HEIGHT = 1024, 768
BLACK = pygame.Color('black')

pygame.init()
pygame.display.set_caption('pygame minimal template')
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

pygame.mouse.set_visible(False)

mouse_group = pygame.sprite.Group()
mouse_image = pygame.image.load(
    files('demos.resources').joinpath('cursor.png')
).convert_alpha()

e_mouse = ecs.create_entity('mouse')
ecs.add_component(e_mouse, Comp.MOUSE, ecsc.Mouse())
ecs.add_component(e_mouse, Comp.POSITION, ecsc.Position(Vector2(0, 0), 0))
ecs.add_component(e_mouse, Comp.SPRITE, ecsc.Sprite(mouse_image, mouse_group))
ecs.add_component(e_mouse, Comp.MOMENTUM, ecsc.Momentum(Vector2(0, 0), phi=30))

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

    screen.fill(BLACK)

    mouse_group.update(dt)
    ecs.run_system(dt, ecsc.mouse_system, Comp.MOUSE, Comp.POSITION)
    ecs.run_system(dt, ecsc.momentum_system, Comp.MOMENTUM, Comp.POSITION)
    ecs.run_system(dt, ecsc.sprite_system, Comp.SPRITE, Comp.POSITION)

    mouse_group.draw(screen)

    pygame.display.update()
    clock.tick(FPS)

pygame.quit()
