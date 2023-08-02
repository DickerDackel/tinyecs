import pygame
import tinyecs as ecs
import tinyecs.components as ecsc

from math import copysign
from random import random
from types import SimpleNamespace

from pgcooldown import Cooldown
from pygame import Vector2


def dead_sprite_system(dt, eid, dead, sprite):
    sprite.kill()
    ecs.remove_entity(eid)


def lifetime_sprite_system(dt, eid, lifetime, sprite):
    if lifetime.hot:
        return
    sprite.kill()
    ecs.remove_entity(eid)


def homing_missile(target, pos, sprite_group):
    sprite = pygame.sprite.Sprite(sprite_group)
    sprite.image = pygame.Surface((8, 8))
    sprite.image.fill('orange')
    sprite.rect = sprite.image.get_rect(center=pos)

    momentum = Vector2(random() * 200 + 200, 0).rotate(random() * 360)

    e = ecs.create_entity()
    ecs.add_component(e, 'position', Vector2(pos))
    ecs.add_component(e, 'sprite', sprite)
    ecs.add_component(e, 'homing_missile', SimpleNamespace(target=target,
                                                           allowed_angle=180,
                                                           prev_los=None))
    ecs.add_component(e, 'lifetime', Cooldown(20))
    ecs.add_component(e, 'momentum', momentum)


def create_shard(position, image, *groups):
    pos = Vector2(position)
    v = Vector2(random() * 250 + 50, 0).rotate(random() * 360)
    sprite = pygame.sprite.Sprite(*groups)
    sprite.image = image
    sprite.rect = image.get_rect(center=pos)

    e = ecs.create_entity()
    ecs.add_component(e, 'position', pos)
    ecs.add_component(e, 'sprite', sprite)
    ecs.add_component(e, 'momentum', v)
    ecs.add_component(e, 'lifetime', Cooldown(random() * 0.25))


def homing_missile_system(dt, eid, homing_missile, position, momentum):
    target_pos = ecs.comp_of_eid(homing_missile.target, 'position')

    target = target_pos
    los = target - position
    los_phi = (los.as_polar()[1] + 360) % 360 - 180

    if los.length() < 16:
        ecs.add_component(eid, 'dead', True)

        image = pygame.Surface((3, 3))
        image.fill('brown')

        parent = ecs.comp_of_eid(eid, 'sprite')
        sprite_groups = parent.groups()

        for i in range(32):
            create_shard(position, image, *sprite_groups)
        return

    if homing_missile.prev_los is None:
        homing_missile.prev_los = los_phi
        return

    delta_phi = ((homing_missile.prev_los - los_phi) + 360) % 360 - 180
    if delta_phi == 0:
        return

    homing_missile.prev_los = los_phi

    rotation = min(homing_missile.allowed_angle * dt, abs(delta_phi))
    momentum.rotate_ip(copysign(rotation, delta_phi))


def fire_system(dt, eid, fire, position):
    for i in range(fire.count):
        fire.fkt(pos=position)

    ecs.remove_component(eid, 'fire')


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


def create_mouse(sprite_group):
    sprite = pygame.sprite.Sprite(sprite_group)
    sprite.image = pygame.Surface((16, 16))
    pygame.draw.circle(sprite.image, 'cyan', (8, 8), 8, width=1)
    sprite.rect = sprite.image.get_rect(center=pygame.mouse.get_pos())

    e = ecs.create_entity('mouse')
    ecs.add_component(e, 'mouse', True)
    ecs.add_component(e, 'sprite', sprite)
    ecs.add_component(e, 'position', Vector2())
    return e


def create_target(sprite_group, world):
    sprite = pygame.sprite.Sprite(sprite_group)
    sprite.image = pygame.Surface((24, 24))
    sprite.image.fill('limegreen')
    sprite.rect = sprite.image.get_rect()

    v = Vector2(150, 0).rotate(random() * 360)

    e = ecs.create_entity('target')
    ecs.add_component(e, 'position', Vector2(random() * world.width,
                                             random() * world.height))
    ecs.add_component(e, 'momentum', v)
    ecs.add_component(e, 'sprite', sprite)
    ecs.add_component(e, 'world', world)
    return e


def main():
    TITLE = 'Homing missile demo'
    FPS = 60
    SCREEN = pygame.Rect(0, 0, 1024, 768)

    pygame.init()
    pygame.display.set_caption(TITLE)
    screen = pygame.display.set_mode(SCREEN.size)
    clock = pygame.time.Clock()
    pygame.mouse.set_visible(False)

    group = pygame.sprite.Group()

    create_mouse(group)
    target = create_target(group, SCREEN)

    def fire_bullet(pos, target, sprite_group):
        sprite = pygame.sprite.Sprite(sprite_group)
        sprite.image = pygame.Surface((1, 1))
        sprite.image.fill('white')
        sprite.rect = sprite.image.get_rect()

        target_pos = ecs.comp_of_eid(target, 'position')
        v = (target_pos - pos).rotate(random() * 10 - 5).normalize() * 500

        e = ecs.create_entity()
        ecs.add_component(e, 'position', Vector2(pos))
        ecs.add_component(e, 'sprite', sprite)
        ecs.add_component(e, 'momentum', v)
        ecs.add_component(e, 'lifetime', Cooldown(1.5))

    autofire_cooldown = Cooldown(0.1)
    autofire = False
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

                case pygame.MOUSEBUTTONDOWN if e.button == 1:
                    for i in range(7):
                        homing_missile(target, e.pos, group)

                case pygame.MOUSEBUTTONDOWN if e.button == 3:
                    autofire = True

                case pygame.MOUSEBUTTONUP if e.button == 3:
                    autofire = False

        if autofire and autofire_cooldown.cold:
            for i in range(7):
                homing_missile(target, e.pos, group)

        screen.fill('black')

        ecs.run_system(dt, ecsc.mouse_system, 'mouse', 'position')
        ecs.run_system(dt, lifetime_sprite_system, 'lifetime', 'sprite')
        ecs.run_system(dt, dead_sprite_system, 'dead', 'sprite')
        ecs.run_system(dt, ecsc.dead_system, 'dead')
        ecs.run_system(dt, ecsc.momentum_system, 'momentum', 'position')
        ecs.run_system(dt, ecsc.sprite_system, 'sprite', 'position')
        ecs.run_system(dt, bounding_box_system, 'world', 'position', 'momentum')
        ecs.run_system(dt, homing_missile_system, 'homing_missile', 'position', 'momentum')
        ecs.run_system(dt, fire_system, 'fire', 'position')

        group.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)
        pygame.display.set_caption(f'{TITLE} - time={pygame.time.get_ticks()/1000:.2f}  fps={clock.get_fps():.2f}')

    pygame.quit()


if __name__ == '__main__':
    main()
