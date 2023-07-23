"""Helpers for tinyecs

For tinyecs, see https://github.com/dickerdackel/tinyecs

Nothing in here couldn't be written yourself in a few minutes, it's just for
convenience.
"""

import pygame
import tinyecs as ecs

from pygame import Vector2


class ESprite(pygame.sprite.Sprite):
    def shutdown_(self):
        self.kill()


def dead_system(dt, eid, dead):
    """Reap entities marked as dead."""
    ecs.remove_entity(eid)


def extension_system(dt, eid, extension):
    """Add additional components.

    Parameters:

        extension       list of tuples consisting of
                            - cooldown when to launch the extension
                            - cid: component ID for the component
                            - comp: the actual component

    Synopsis:

        To add a Vector2 component 'momentum' after 5 seconds

        extensions = [
            (5, 'momentum', Vector2(100, 0)),
            ...
        ]

    """
    kill_list = []
    for e in extension:
        (cooldown, cid, comp) = e
        if cooldown.cold:
            ecs.add_component(eid, cid, comp)
            kill_list.append(e)

    for e in kill_list:
        extension.remove(e)

    if len(extension) == 0:
        ecs.remove_component(eid, 'extension')


def force_system(dt, eid, force, momentum):
    """Apply a force to a momentum"""
    momentum += force * dt


def friction_system(dt, eid, friction, momentum):
    """Apply frictoin to a momentum.

    In contrast to a force, which adds a directional vector to the momentum,
    the friction scales the momentum by a factor.  Thus Can also be greater 1.

    """
    momentum *= friction ** dt


def lifetime_system(dt, eid, lifetime):
    """Kill an entity after a specified time"""
    if lifetime.cold:
        ecs.remove_entity(eid)


def momentum_system(dt, eid, momentum, position):
    """Apply momentum to a position (a.k.a. "move")."""
    position += momentum * dt


def mouse_system(dt, eid, mouse, position):
    """Place the position of an entity to the mouse cursor."""
    mp = pygame.mouse.get_pos()
    position.xy = Vector2(mp)


def sprite_system(dt, eid, sprite, position):
    """Set the rect.center of sprite to position."""

    if sprite.rect:
        sprite.rect.center = position.xy
    else:
        sprite.rect = sprite.image.get_rect(center=position)
