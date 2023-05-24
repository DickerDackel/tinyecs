import pygame
import tinyecs as ecs

from cooldown import Cooldown
from dataclasses import dataclass
from enum import Enum, auto
from math import copysign
from random import random, randint
from pygame.math import Vector2

FPS = 60
SCREEN_WIDTH, SCREEN_HEIGHT = 1024, 768
BLACK = pygame.Color('black')
MAX_SPEED = 150

pygame.init()
pygame.display.set_caption('pygame minimal template')
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
pygame.mouse.set_visible(False)


class Comp(Enum):
    CLEANUP = auto()
    MOMENTUM = auto()
    NAME = auto()
    POSITION = auto()
    RENDERABLE = auto()
    SCREEN = auto()
    SPRITE = auto()
    TARGET = auto()
    THRUST = auto()


class Position(Vector2): pass
class Momentum(Vector2): pass
class Color(pygame.Color): pass


@dataclass
class Thrust:
    """A thrust component

    speed: linear speed as a Vector with length and direction
    angular_speed: rotation speed
    """
    delay: Cooldown
    speed: Vector2
    angular_speed: float
    clamp: float


class MySprite(pygame.sprite.Sprite):
    def __init__(self, *groups):
        super().__init__(*groups)
        color = pygame.Color(randint(0, 255), randint(0, 255), randint(0, 255))
        self.image = pygame.Surface((randint(10, 32), randint(10, 32)))
        self.image.fill(color)
        self.rect = self.image.get_rect()


def motion_system(dt, eid, position, momentum, sprite):
    position += momentum * dt

    r = sprite.rect
    r.center = position

    if r.left < 0 and momentum.x < 0:
        momentum.x = -momentum.x
        r.centerx += momentum.x * dt
    elif r.right >= SCREEN_WIDTH and momentum.x > 0:
        momentum.x = -momentum.x
        r.centerx += momentum.x * dt
    if r.top < 0 and momentum.y < 0:
        momentum.y = -momentum.y
        r.centery += momentum.y * dt
    elif r.bottom >= SCREEN_HEIGHT and momentum.y > 0:
        momentum.y = -momentum.y
        r.centery += momentum.y * dt

    # Re-assign corrected rect position back to position
    #
    # DANGER: must not assign to position object!  This is an object reference
    # and the original object would not be updated this way.
    position.x, position.y = r.center


def hunter_system(dt, eid, screen, target, position, momentum, thrust):
    if not thrust.delay.cold:
        return

    blast_radius = 50

    current_direction = momentum.copy()
    target_vector = Vector2(target.rect.center) - position

    if target_vector.length() < blast_radius:
        ecs.add_component(eid, Comp.CLEANUP, True)
        return

    wanted_angle = current_direction.angle_to(target_vector)
    if wanted_angle > 180:
        wanted_angle -= 360

    new_direction = current_direction.rotate(copysign(thrust.angular_speed * dt, wanted_angle))
    accelleration = new_direction.normalize() * thrust.speed
    new_direction += accelleration
    new_direction.clamp_magnitude_ip(thrust.clamp)
    momentum.x = new_direction.x
    momentum.y = new_direction.y


def cleanup_system(dt, eid, cleanup, sprite):
    sprite.kill()
    ecs.remove_entity(eid)


def launch(screen, target, group):
    def create_sprite():
        surface = pygame.Surface((randint(10, 32), randint(10, 32)))
        color = pygame.Color(randint(0, 255), randint(0, 255), randint(0, 255))
        surface.fill(color)
        rect = surface.get_rect()
        return surface, rect

    image, rect = create_sprite()
    v = Vector2(random() * 200 + 250, 0)
    v.rotate_ip(random() * 360)

    e = ecs.create_entity()
    ecs.add_component(e, Comp.NAME, 'Joe')
    ecs.add_component(e, Comp.POSITION, Position(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
    ecs.add_component(e, Comp.MOMENTUM, Momentum(v))
    ecs.add_component(e, Comp.SCREEN, screen)
    ecs.add_component(e, Comp.SPRITE, MySprite(group))
    ecs.add_component(e, Comp.TARGET, target)
    ecs.add_component(e, Comp.THRUST, Thrust(delay=Cooldown(random() * 0.25 + 0.25), speed=15, angular_speed=360, clamp=1500))


group = pygame.sprite.Group()
ecs.add_system(motion_system, Comp.POSITION, Comp.MOMENTUM, Comp.SPRITE)
ecs.add_system(hunter_system, Comp.SCREEN, Comp.TARGET, Comp.POSITION, Comp.MOMENTUM, Comp.THRUST)
ecs.add_system(cleanup_system, Comp.CLEANUP, Comp.SPRITE)


class Mouse(pygame.sprite.Sprite):
    def __init__(self, *groups):
        super().__init__(*groups)
        self.image = pygame.Surface((32, 32))
        pygame.draw.circle(self.image, pygame.Color('yellow'), (15, 15), 8)
        self.rect = self.image.get_rect(center=pygame.mouse.get_pos())

    def update(self, dt):
        self.rect.center = pygame.mouse.get_pos()


mouse = Mouse(group)

for i in range(16):
    launch(screen, mouse, group)

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
                            launch(screen, mouse, group)

    screen.fill(BLACK)

    group.update(dt)
    ecs.run_all_systems(dt)

    group.draw(screen)
    pygame.display.flip()
    clock.tick(FPS)
    pygame.display.set_caption(f'FPS: {clock.get_fps():5.2f} @ {len(ecs.eidx):05d} sprites')

pygame.quit()
