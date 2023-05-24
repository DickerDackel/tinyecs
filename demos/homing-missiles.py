import pygame
import tinyecs as ecs
import tinyecs.components as ecsc

from importlib.resources import files
from pygame.math import Vector2
from random import random
from types import SimpleNamespace

from tinyecs.components import Comp

FPS = 60
SCREEN_WIDTH, SCREEN_HEIGHT = 1024, 768
BLACK = pygame.Color('black')

pygame.init()
pygame.display.set_caption('pygame minimal template')
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
pygame.mouse.set_visible(False)


sprite_group = pygame.sprite.Group()

missile_image = pygame.image.load(
    files('demos.resources').joinpath('missile.png')
).convert_alpha()
missile_image = pygame.transform.rotate(missile_image, -90)

player_image = pygame.Surface((32, 32), flags=pygame.SRCALPHA)
pygame.draw.circle(player_image, pygame.Color('red'), (15, 15), 10)
player_image = pygame.transform.rotate(player_image, -90)
player_sprite = ecsc.Sprite(player_image, sprite_group)

player = ecs.create_entity('player')
ecs.add_component(player, Comp.POSITION, ecsc.Position(phi=90))
ecs.add_component(player, Comp.MOMENTUM, ecsc.Momentum())
ecs.add_component(player, Comp.SPRITE, player_sprite)
ecs.add_component(player, Comp.MOUSE, True)

target_image = pygame.Surface((32, 32), flags=pygame.SRCALPHA)
pygame.draw.circle(target_image, pygame.Color('blue'), (15, 15), 10)
target_image = pygame.transform.rotate(target_image, -90)
target_sprite = ecsc.Sprite(target_image, sprite_group)

target = ecs.create_entity()
ecs.add_component(target, Comp.POSITION, ecsc.Position((50, SCREEN_HEIGHT // 2)))
ecs.add_component(target, Comp.MOMENTUM, ecsc.Momentum((150, 0)))
ecs.add_component(target, Comp.SPRITE, target_sprite)
ecs.add_component(target, Comp.CONTAINER, screen.get_rect())


def launch_missile():
    pos = ecs.comp_of_eid(player, Comp.POSITION).v

    speed = random() * 500 + 50
    direction = random() * 360
    v = Vector2()
    v.from_polar((speed, direction))

    missile_sprite = ecsc.Sprite(missile_image, sprite_group)
    missile = ecs.create_entity()
    ecs.add_component(missile, Comp.POSITION, ecsc.Position(pos, phi=direction))
    ecs.add_component(missile, Comp.MOMENTUM, ecsc.Momentum(v))
    ecs.add_component(missile, Comp.THRUST, SimpleNamespace(speed=500, phi=180))
    ecs.add_component(missile, Comp.SPRITE, missile_sprite)
    ecs.add_component(missile, Comp.TARGET, target)


ecs.add_system(ecsc.mouse_system, Comp.MOUSE, Comp.POSITION)
ecs.add_system(ecsc.momentum_system, Comp.POSITION, Comp.MOMENTUM)
ecs.add_system(ecsc.sprite_system, Comp.SPRITE, Comp.POSITION)
ecs.add_system(ecsc.target_system, Comp.TARGET, Comp.THRUST, Comp.MOMENTUM, Comp.POSITION)
ecs.add_system(ecsc.dead_system, Comp.DEAD)
ecs.add_system(ecsc.sprite_cycle_system, Comp.SPRITE, Comp.SPRITE_CYCLE)
ecs.add_system(ecsc.bounding_box_system, Comp.CONTAINER, Comp.SPRITE,
               Comp.POSITION, Comp.MOMENTUM)

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
            case pygame.MOUSEBUTTONDOWN:
                for i in range(7):
                    launch_missile()

    screen.fill(BLACK)

    ecs.run_all_systems(dt)

    sprite_group.update(dt)
    sprite_group.draw(screen)

    pygame.display.flip()
    clock.tick(FPS)
    pygame.display.set_caption(f'FPS: {clock.get_fps():5.2f} @ {len(ecs.eidx):05d} sprites')

pygame.quit()
