import pygame
import tinyecs as ecs
import tinyecs.components as tec

from tinyecs.components import Comp

FPS = 60
SCREEN_WIDTH, SCREEN_HEIGHT = 1024, 768
BLACK = pygame.Color('black')

pygame.init()
pygame.display.set_caption('pygame minimal template')
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

sprites = pygame.sprite.Group()

surface = pygame.Surface((32, 32), flags=pygame.SRCALPHA)
pygame.draw.polygon(surface,
                    pygame.Color('white'),
                    [(15, 26), (0, 31), (15, 0), (31, 31), (15, 26)],
                    width=2)
surface = pygame.transform.rotate(surface, -90)
spr = tec.Sprite(surface, sprites)

player = ecs.create_entity()
ecs.add_component(player, Comp.POSITION, tec.Position((SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,)))
ecs.add_component(player, Comp.SPRITE, spr)
ecs.add_component(player, Comp.MOMENTUM, tec.Momentum((0, 0)))
ecs.add_component(player, Comp.FRICTION, tec.Force((50, 0), active=True))
ecs.add_component(player, Comp.THRUST, tec.Force((150, 0), active=False))
ecs.add_component(player, Comp.CONTAINER, tec.Container(screen.get_rect()))

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
                        comp = ecs.comps_of_eid(player, Comp.THRUST)[0]
                        comp.active = True
                        print(ecs.eidx[player])
                    case pygame.K_a:
                        comp = ecs.comps_of_eid(player, Comp.MOMENTUM)[0]
                        comp.phi = 180
                    case pygame.K_d:
                        comp = ecs.comps_of_eid(player, Comp.MOMENTUM)[0]
                        comp.phi = -180

            case pygame.KEYUP:
                match e.key:
                    case pygame.K_SPACE:
                        comp = ecs.comps_of_eid(player, Comp.THRUST)[0]
                        comp.active = False
                        print(ecs.eidx[player])
                    case pygame.K_a:
                        comp = ecs.comps_of_eid(player, Comp.MOMENTUM)[0]
                        comp.phi = 0
                    case pygame.K_d:
                        comp = ecs.comps_of_eid(player, Comp.MOMENTUM)[0]
                        comp.phi = 0

    screen.fill(BLACK)

    ecs.run_system(dt, tec.thrust_system, Comp.THRUST, Comp.POSITION, Comp.MOMENTUM)
    ecs.run_system(dt, tec.friction_system, Comp.FRICTION, Comp.MOMENTUM)
    ecs.run_system(dt, tec.momentum_system, Comp.POSITION, Comp.MOMENTUM)
    ecs.run_system(dt, tec.sprite_system, Comp.SPRITE, Comp.POSITION)
    ecs.run_system(dt, tec.wrap_around_system, Comp.CONTAINER, Comp.SPRITE, Comp.POSITION, Comp.MOMENTUM)

    sprites.draw(screen)

    pygame.display.update()
    clock.tick(FPS)

pygame.quit()
