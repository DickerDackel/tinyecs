import colorsys
import pygame
import tinyecs as ecs

from collections import deque
from random import random
from types import SimpleNamespace

from cooldown import Cooldown
from pygame import Vector2


def marquee_system(dt, eid, marquee, border, surface):
    def bounce(point, momentum):
        point += momentum * dt
        if point.x < 0:
            point.x = -point.x
            momentum.x = -momentum.x
        elif point.x > border.right:
            point.x = 2 * border.right - point.x
            momentum.x = -momentum.x
        if point.y < 0:
            point.y = -point.y
            momentum.y = -momentum.y
        elif point.y > border.bottom:
            point.y = 2 * border.bottom - point.y
            momentum.y = -momentum.y

    bounce(marquee.v0, marquee.speed0)
    bounce(marquee.v1, marquee.speed1)

    marquee.t = (marquee.t + dt) % 1
    color = [int(c * 255) for c in colorsys.hsv_to_rgb(marquee.t, 1, 1)]

    if marquee.delay.cold:
        marquee.delay.reset()
        marquee.deque.append((color, marquee.v0.copy(), marquee.v1.copy()))

    pygame.draw.line(surface, color, marquee.v0, marquee.v1, width=1)
    for color, v0, v1 in marquee.deque:
        pygame.draw.line(surface, color, v0, v1, width=1)


def main():
    TITLE = 'pygame minimal template'
    FPS = 60
    SCREEN = pygame.Rect(0, 0, 1024, 768)
    BLACK = pygame.Color('black')

    pygame.init()
    pygame.display.set_caption(TITLE)
    screen = pygame.display.set_mode(SCREEN.size)
    clock = pygame.time.Clock()
    pygame.mouse.set_visible(False)

    ecs.add_system('marquee', 'border', 'surface')

    e = ecs.create_entity()
    ecs.add_component(e, 'marquee', SimpleNamespace(v0=Vector2(random() * SCREEN.width, random() * SCREEN.height),
                                                    v1=Vector2(random() * SCREEN.width, random() * SCREEN.height),
                                                    speed0=Vector2(random() * 50 + 100),
                                                    speed1=Vector2(random() * 50 + 100),
                                                    deque=deque(maxlen=16),
                                                    delay=Cooldown(0.1),
                                                    t=0))
    ecs.add_component(e, 'border', SCREEN)
    ecs.add_component(e, 'surface', screen)

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

        ecs.run_system(dt, marquee_system, 'marquee', 'border', 'surface')

        pygame.display.flip()
        clock.tick(FPS)
        pygame.display.set_caption(f'{TITLE} - time={pygame.time.get_ticks()/1000:.2f}  fps={clock.get_fps():.2f}')

    pygame.quit()


if __name__ == '__main__':
    main()
