import pygame
import tinyecs as ecs

from random import random
from types import SimpleNamespace
from pygame import Vector2


def momentum_system(dt, eid, momentum, position):
    position += momentum * dt


def border_system(dt, eid, border, position, momentum):
    if position.x < 0:
        position.x = -position.x
        momentum.x = -momentum.x
    elif position.x > border.right:
        position.x = 2 * border.right - position.x
        momentum.x = -momentum.x
    if position.y < 0:
        position.y = -position.y
        momentum.y = -momentum.y
    elif position.y > border.bottom:
        position.y = 2 * border.bottom - position.y
        momentum.y = -momentum.y


def background_system(dt, eid, background, position, surface):
    def draw_one(angle, offset):
        v0 = Vector2(position)
        v1 = Vector2(2000, 0).rotate(angle)
        pygame.draw.line(surface, 'grey30', v0 + offset, v0 + v1 + offset, width=1)
        pygame.draw.line(surface, 'grey30', v0 + offset, v0 - v1 + offset, width=1)

    angle = background.angle
    step = Vector2(250, 0).rotate(angle + 90)
    for i in range(10):
        draw_one(angle, step * i)
        draw_one(angle, -step * i)

    background.angle = (background.angle + background.speed * dt) % 360
    pygame.draw.circle(surface, 'yellow', position, 3)


def main():
    TITLE = 'pygame minimal template'
    FPS = 60
    SCREEN = pygame.Rect(0, 0, 1024, 768)

    pygame.init()
    pygame.display.set_caption(TITLE)
    screen = pygame.display.set_mode(SCREEN.size)
    clock = pygame.time.Clock()
    pygame.mouse.set_visible(False)

    ecs.add_system(momentum_system, 'momentum', 'position')
    ecs.add_system(border_system, 'border', 'position', 'momentum')
    ecs.add_system(background_system, 'background', 'position', 'surface')

    for i in range(3):
        e = ecs.create_entity()
        ecs.add_component(e, 'background', SimpleNamespace(angle=random() * 360, speed=random() * 45))
        ecs.add_component(e, 'surface', screen)
        ecs.add_component(e, 'position', Vector2(SCREEN.center))
        ecs.add_component(e, 'momentum', Vector2(50, 0).rotate(random() * 360))
        ecs.add_component(e, 'border', SCREEN)

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

        screen.fill('black')

        ecs.run_all_systems(dt)

        pygame.display.flip()
        clock.tick(FPS)

        entities = len(ecs.eidx)
        fps = clock.get_fps()
        pygame.display.set_caption(f'{TITLE} - {fps:.2f}  {entities=}')

    pygame.quit()


if __name__ == '__main__':
    main()
