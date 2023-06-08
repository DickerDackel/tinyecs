"""Helpers for tinyecs

For tinyecs, see https://github.com/dickerdackel/tinyecs

Nothing in here couldn't be written yourself in a few minutes, it's just for
convenience.

This said, here's the list of Comp IDs, Classes and systems provided:

Comp IDs:

Please note, that a component ID in tinyecs can be just any hashable data,
since in the backend, tinyecs is just a bunch of dicts.  If you want to roll
your own component ID scheme, there is nothing special about the things defined
here, just do your own.

    * EXTENSION
        - A component adding more components to its entity at a later time.  It
          contains an initial delay and the list of components to add
    * POSITION
        - A component to hold x/y coordinates, an orientation angle
    * MOMENTUM
        - A component for momentum, holding a directional vector, angular
          speed and clamps to limit both.
    * FORCE, FRICTION, THRUST
        - A directional force.  It holds a vector for the force and a flag
          to switch it on/off
    * MOUSE
        - Marking the entity as dependent on the mouse position.  See
          system_mouse.
    * HEALTH
        - Only holds a float for tracking health
    * SCORE
        -  Like health, just holds a float
    * TARGET
        - A component to hold the eid of another entity
    * SPRITE
        - directly derived from pygame.sprite.Sprite
    * SPRITE_CYCLE
        - A component holding a frame animation
    * DEAD
        - This class is just a flag and doesn't hold any data.
    * CONTAINER
        - Directly derived from pygame.Rect

Classes:

As noted in tinyecs docs, a component can be just about any datatype.  But
since datatypes like int and float are passed by value, it's useful to wrap
even single data components into a class, otherwise they cannot be written to
by a system.

See the documentation of the actual classes below for what they are.

    * Extension
    * Position
    * Momentum
    * Force
    * Mouse
    * Health
    * Score
    * Target
    * Sprite
    * SpriteCycle
    * Dead
    * Container

Systems:

    * extension_system(dt, eid, comps):
        if the initial delay is passed, add all components to the entity
        also removes the Extension component.

    * momentum_system(dt, eid, position, momentum
        apply the momentup component to the position component

    * force_system(dt, eid, force, momentum):
    * thrust_system(dt, eid, force, position, momentum):
    * friction_system(dt, eid, force, momentum):
        Used in Comp.FORCE, Comp.FRICTION, Comp.THRUST
        Apply a force to the momentum component
        - force_system uses the force as is, e.g. Gravity
        - friction_system applies the value of the force in negative momentum direction
        - thrust_system applies the value of the force in the direction of the position comps phi

    * mouse_system(dt, eid, mouse, position):
        If an entity contains a mouse component, the current mouse position is
        fetched from pygame.mouse and put into the position comp

    * sprite_system(dt, eid, sprite, position):

       The sprite comp is directly derived from pygame.sprite.Sprite and
       expected to be placed into a sprite group for rendering.

       The position will be applied to sprite.rect.center

       If position.phi is not 0, the initial sprite.image is saved as base
       image, and a rotated version will be assigned to sprite.image.  The
       rotated image will be put into a cache, so every rotation will take
       place only once.  The rect will be updated accordingly.

       This will currently *not* work with sprite_cycle_system.

    * sprite_cycle_system(dt, eid, sprite, sprite_cycle):

        Ths sprite.image comp will be updated according to the
        sprite_cycle.delay with a cycle of sprite_cycle.images.

        This is currently *not* compatible with the rotation of the
        sprite_system.

    * dead_system(dt, eid, dead):

        If an entity is marked as dead, running this system will remove the
        entity from the tinyecs registry.

        Note, that this is just a raw base implementation that just cleans up
        the ECS, but doesn't care about sprites in sprite groups, ...

    * bounding_box_system(dt, eid, container, sprite, position, momentum)

        Make a sprite bound from the edge of a container, e.g. a screen rect.
        momentum will be deflected, position will be corrected.

    * wrap_around_system(dt, eid, container, sprite, position, momentum):

        Make the sprite wrap around the edge of a container, think Asteroids.
        position will be corrected.

    * target_system(dt, eid, target_eid, position, momentum):

        Make an entity follow a target entity.

        This will request the target entities position, calculate how to
        correct course and modify the momentum accordingly to move towards the
        target.
"""

import pygame
import tinyecs as ecs

from dataclasses import dataclass, field, InitVar
from enum import Enum, auto
from itertools import cycle
from math import copysign

from cooldown import Cooldown
from pygame.math import Vector2


class Comp(Enum):
    EXTENSION = auto()
    POSITION = auto()
    MOMENTUM = auto()
    ANGULAR_MOMENTUM = auto()
    FORCE = auto()
    FRICTION = auto()
    MOUSE = auto()
    HEALTH = auto()
    SCORE = auto()
    TARGET = auto()
    THRUST = auto()
    SPRITE = auto()
    SPRITE_CYCLE = auto()
    DEAD = auto()
    CONTAINER = auto()


@dataclass
class Extension:
    """A component carrying a list of components to add later

        Extension(delay, components)

    Arguments
        delay       A Cooldown object to wait before extending
        components  A dict of {cid: component, ...} to extend with

    """
    delay: Cooldown
    components: dict


def extension_system(dt, eid, extension):
    """add predefined components to the current entity

        tinyecs.add_system(extension_system, Comp.EXTENSION)
        tinyecs.run_system(extension_system, Comp.EXTENSION)

    Arguments:

        dt          delta time
        eid         entity id
        components  dict of {component_id: component, ...}

    This system adds the defined additional components to the entity specified
    by eid, and removes itself from the entities' components.
    """
    if not extension.delay.cold:
        return

    for cid, c in extension.components.items():
        ecs.add_component(eid, cid, c)

    ecs.remove_component(eid, Comp.EXTENSION)


@dataclass
class Position:
    """A component representing a position inside the game world

        Position(tuple, phi=0)

    Arguments
        tuple       (x, y) position
        phi         The direction the object is pointing towards

    Attributes:
        v       The position as Vector2, created from tuple
        phi     Rotation of the entity, default is 0, ccw is positive
    """
    t: InitVar[tuple] = (0, 0)
    phi: float = 0
    v: Vector2 = field(init=False, default_factory=Vector2)

    def __post_init__(self, t):
        self.v = Vector2(t)


@dataclass
class Momentum:
    """A component representing the momentum of an entity

        Momentum(tuple)

    Arguments:

        tuple       (dx, dy) linear momentum

    Attributes:

        v           The linear momentum vector in game units per second, created from tuple
        phi         The angular momentum in degrees per second
        clamp_v     Maximum linear momentum (think air resistance)
        clamp_phi   Maximum angular momentum
    """
    t: InitVar[tuple] = (0, 0)
    phi: float = 0
    clamp_v: float = 0
    clamp_phi: float = 0
    v: Vector2 = field(init=False, default_factory=Vector2)

    def __post_init__(self, t):
        self.v = Vector2(t)


def momentum_system(dt, eid, position, momentum):
    """apply linear and angular momentum to the position of an entity

        tinyecs.add_system(momentum_system, Comp.POSITION, Comp.MOMENTUM)
        tinyecs.run_system(momentum_system, Comp.POSITION, Comp.MOMENTUM)

    Arguments:

        dt          delta time
        eid         entity id
        position    the position component
        momentum    the momentum component

    This class modifies the position component by means of the momentum
    component.
    """
    if momentum.clamp_v and momentum.v.length() > momentum.clamp_v:
        momentum.v.scale_to_length(momentum.clamp_v)

    if momentum.clamp_phi and abs(momentum.phi) > momentum.clamp_phi:
        momentum.phi = copysign(momentum.clamp_phi, momentum.phi)

    # Since screen(0, 0) is top-left, mirror y-momentum
    position.v += momentum.v * dt
    position.phi += momentum.phi * dt


@dataclass
class Force:
    """A component representing a forcFe on an object e.g. thrust or gravity

        Force(tuple)

    Arguments:

        tuple       (dx, dy) force vector

    Attributes:

        v           The force vector, measured in game units per second, created from tuple
        active      on/off switch for the component

    systems can use this component to apply a force to a momentum, e.g.
    gravity, friction, thrust.
    """
    t: InitVar[tuple]
    active: bool = True
    v: Vector2 = field(default_factory=Vector2)

    def __post_init__(self, t):
        self.v = Vector2(t)


def force_system(dt, eid, force, momentum):
    """apply force to the momentum of an entity

        tinyecs.add_system(force_system, Comp.FORCE, Comp.MOMENTUM)
        tinyecs.run_system(force_system, Comp.FORCE, Comp.MOMENTUM)

    Arguments:

        dt                  delta time
        eid                 entity id
        force               the force to apply, in units per second
        momentum            the momentum component

    This system adds the force to the momentum, so a motion system will apply
    that.  This can be used for gravity or friction.

    Note, that there is a dedicated thrust_system that only uses the length of
    the force vector and takes the angle from the position component's phi
    attribute.
    """
    if not force.active:
        return

    momentum.v += force.v * dt


def thrust_system(dt, eid, force, position, momentum):
    """apply thrust to the current momentum.

        tinyecs.add_system(thrust_system, Comp.THRUST, Comp.POSITION, Comp.MOMENTUM)
        tinyecs.run_system(thrust_system, Comp.THRUST, Comp.POSITION, Comp.MOMENTUM)

    Arguments:

        dt          delta time
        eid         entity id
        thrust      the amount of thrust that is to be applied
        position    the position component
        momentum    the momentum component

    This system creates a thrust vector from the position.phi angle and the
    thrust.amount force.  This vector is then added to the current momentum.

    Thrust can be enabled or disabled by assigning to thrust.enabled.
    """
    if not force.active:
        return

    v = Vector2()
    v.from_polar((force.v.length(), position.phi))
    v.y = -v.y
    momentum.v += v * dt


def friction_system(dt, eid, force, momentum):
    """apply thrust to the current momentum.

        tinyecs.add_system(friction_system, Comp.THRUST, Comp.POSITION, Comp.MOMENTUM)
        tinyecs.run_system(friction_system, Comp.THRUST, Comp.POSITION, Comp.MOMENTUM)

    Arguments:

        dt          delta time
        eid         entity id
        force       the amount of thrust that is to be applied
        momentum    the momentum component

    This system differs to the force_system in that it reduces the momentum's
    value by a fixed amount of units per second until it is zero.
    """
    if not force.active:
        return

    lm = momentum.v.length()
    lf = force.v.length() * dt
    l = lm - lf
    if l > 0:
        momentum.v.scale_to_length(l)
    else:
        momentum.v.x = momentum.v.y = 0


@dataclass
class Mouse:
    """A component representing the mouse position

        Mouse()

    Arguments/Attributes:

        v       The mouse position vector in pixels

    This is only a container.  The contents must be updated by running the
    mouse_system.
    """
    pass


def mouse_system(dt, eid, mouse, position):
    """Update a position component with the mouse position

        tinyecs.add_system(mouse_system, Comp.MOUSE, Comp.POSITION)
        tinyecs.run_system(mouse_system, Comp.MOUSE, Comp.POSITION)

    Arguments:

        dt                  delta time
        eid                 entity id
        mouse               mouse component
        position            position component to update

    The mouse component doesn't contain any data, it's only an identifyer.
    Entities with that component will have their position updated with the
    current mouse coordinates.
    """
    pos = pygame.mouse.get_pos()
    position.v.x = pos[0]
    position.v.y = pos[1]


@dataclass
class Health:
    """A component representing the health of the entity

        Healt(health)

    Arguments/Attributes:

        health      The actual health

    Long description
    """
    health: float = 0


@dataclass
class Score:
    """A component representing the score worth of the entity

        Score(score)

    Arguments/Attributes:

        score      The actual score

    Long description
    """
    score: float = 0


@dataclass
class Target:
    """The entity is hunting a target object

        Target(eid)

    Arguments/Attributes:

        eid         Entity ID of target

    This class only contains the id of the target entity.  The actual tracking
    takes place in an appropriate system, most likely registered for Comp.FORCE
    and Comp.TARGET.
    """
    eid: str


class Sprite(pygame.sprite.Sprite):
    """A component holding a pygame sprite object to render
        Sprite(image, *groups)

    Arguments/Attributes:

        image      The initial image of the sprite

    This component only holds the sprite (consisting of an sprite.image and a
    sprite.rect as well as sprite groups it's contained in)

    Modification of the image or position of the sprite needs to be done by the
    system and probably other components like a sprite image cycle.
    """
    def __init__(self, image, *groups):
        super().__init__(*groups)
        self.image = image
        self.rect = self.image.get_rect()


def sprite_system(dt, eid, sprite, position):
    """apply the position component to the sprite component

        tinyecs.add_system(sprite_system, Comp.SPRITE, Comp.POSITION)
        tinyecs.run_system(sprite_system, Comp.SPRITE, Comp.POSITION)

    Arguments:

        dt                  delta time
        eid                 entity id
        sprite              the pygame.sprite.Sprite component
        position            the eid's position

    Run this to update the sprite before rendering
    """

    # FIXME / TODO:
    # Make this work with sprite animation, so the cache will need to keep
    # track of different base sprites in all angles.

    if not hasattr(sprite, 'cache'):
        sprite.cache = {}
        sprite.cache[0] = sprite.image

    phi = int(position.phi)
    if phi not in sprite.cache:
        sprite.cache[phi] = pygame.transform.rotate(sprite.cache[0], phi)

    sprite.image = sprite.cache[phi]
    sprite.rect = sprite.image.get_rect(center=position.v)


@dataclass
class SpriteCycle:
    """A component containing a list of images to cycle in a fixed interval

        SpriteCycle(image_list, cooldown)

    Arguments/Attributes:

        image_list      A list of pygame.Surface objects
        cooldown        The delay between cycling through the images
        image_iter      The iterator that cycles over the images

    Long description
    """
    image_list: list[pygame.Surface] = field(default_factory=list)
    cooldown: Cooldown = None
    once: bool = False
    image_iter: iter = field(init=False)

    def __post_init__(self):
        if self.once:
            self.image_iter = iter(self.image_list)
        else:
            self.image_iter = cycle(self.image_list)
        next(self.image_iter)

        if self.cooldown is None:
            self.cooldown = Cooldown(1 / len(self.image_list))


def sprite_cycle_system(dt, eid, sprite, sprite_cycle):
    """an animation cycle for sprites

        tinyecs.add_system(sprite_cycle_system, Comp.SPRITE, Comp.SPRITE_CYCLE)
        tinyecs.run_system(sprite_cycle_system, Comp.SPRITE, Comp.SPRITE_CYCLE)

    Arguments:

        dt                  delta time
        eid                 entity id
        sprite              the pygame.sprite.Sprite component
        sprite_cycle        the sprite_cycle component carrying the images and delay

    Cycle a sprite over a list of images at a constant time
    """
    if not sprite_cycle.cooldown.cold:
        return

    sprite_cycle.cooldown.reset()

    try:
        sprite.image = next(sprite_cycle.image_iter)
        print(f'new image {sprite.image}')
    except StopIteration:
        sprite.kill()
        sprite_cycle.cooldown.reset()
        sprite_cycle.cooldown.pause()
        ecs.remove_entity(eid)

    sprite.rect = sprite.image.get_rect(center=sprite.rect.center)


class Dead:
    """A component identifying if the entity is dead

        Dead(False)

    Arguments/Attributes:

        dead        Is the object dead?

    """
    dead: bool = False


def dead_system(dt, eid, dead):
    """remove an entity from the ecs

        tinyecs.add_system(dead_system, Comp.DEAD)
        tinyecs.run_system(dead_system, Comp.DEAD)

    Arguments:

        dt                  delta time
        eid                 entity id
        dead                The component identifying this sprite as dead

    If an entity is marked as dead, remove it from the ecs
    """
    try:
        sprite = ecs.comp_of_eid(eid, Comp.SPRITE)
    except ecs.UnknownComponentError:
        pass
    else:
        sprite.kill()

    if dead:
        ecs.remove_entity(eid)


class Container(pygame.Rect):
    """A container for the entity.  This is subclassed from pygame.rect.Rect.

        Container(pygame_Rect_args)

    Arguments/Attributes:

        see pygame.rect.Rect

    """


def bounding_box_system(dt, eid, container, sprite, position, momentum):
    """Keep the entity within the bounding box, reflecting from walls.

        tinyecs.add_system(bounding_box_system, Comp.CONTAINER, Comp.SPRITE, Comp.POSITION, Comp.MOMENTUM)
        tinyecs.run_system(bounding_box_system, Comp.CONTAINER, Comp.SPRITE, Comp.POSITION, Comp.MOMENTUM)

    Arguments:

        dt          delta time
        eid         entity id
        position    the position component
        momentum    the momentum component

    """
    r = sprite.rect.copy()
    r.center = position.v

    if container.contains(r):
        return

    if r.left < 0:
        fix_x = -r.left
        momentum.v.x = -momentum.v.x
    elif r.right > container.right:
        fix_x = -(r.right - container.right)
        momentum.v.x = -momentum.v.x
    else:
        fix_x = 0

    if r.top < 0:
        fix_y = -r.top
        momentum.v.y = -momentum.v.y
    elif r.bottom > container.bottom:
        fix_y = -(r.bottom - container.bottom)
        momentum.v.y = -momentum.v.y
    else:
        fix_y = 0

    position.v.x += fix_x
    position.v.y += fix_y


def wrap_around_system(dt, eid, container, sprite, position, momentum):
    r = sprite.rect.copy()
    r.center = position.v

    if container.contains(r):
        return

    if r.left < 0 and momentum.v.x < 0:
        position.v.x += container.width
    elif r.right >= container.right and momentum.v.x > 0:
        position.v.x -= container.width

    print(f'{r.top} < 0?  {momentum.v.y} < 0?')
    print(f'{r.bottom} >= {container.bottom}?  {momentum.v.y} > 0?')
    if r.top < 0 and momentum.v.y < 0:
        print(f'{position.v.y} -> ', end='')
        position.v.y += container.height
        print(f'{position.v.y}')
    elif r.bottom >= container.bottom and momentum.v.y > 0:
        print(f'{position.v.y} -> ', end='')
        position.v.y -= container.height
        print(f'{position.v.y}')


def target_system(dt, eid, target_eid, thrust, momentum, position):
    """apply acceleration towards a target on the momentum

        tinyecs.add_system(target_system, Comp.TARGET, Comp.THRUST, Comp.MOMENTUM, Comp.POSITION)
        tinyecs.run_system(target_system, Comp.TARGET, Comp.THRUST, Comp.MOMENTUM, Comp.POSITION)

    Arguments:

        dt                  delta time
        eid                 entity id
        target_eid          the eid of the target
        thrust              contains speed and phi
        momentum            contains current linear and angular momentum
        position            the eid's position

    long description...
    """
    blast_radius = 50

    missile = position.v
    target = ecs.comp_of_eid(target_eid, Comp.POSITION).v
    target_vector = target - missile
    target_vector.y = -target_vector.y

    if target_vector.length() < blast_radius:
        ecs.add_component(eid, Comp.DEAD, True)

    missile_angle = position.phi
    target_angle = (target_vector.as_polar()[1] + 180) % 360 - 180
    delta_angle = ((target_angle - missile_angle) + 180) % 360 - 180
    allowed_rotation = copysign(min(abs(delta_angle), thrust.phi * dt), delta_angle)
    position.phi = (position.phi + allowed_rotation) % 360

    applied_thrust = Vector2()
    applied_thrust.from_polar((thrust.speed, position.phi))
    applied_thrust.y = -applied_thrust.y
    momentum.v = applied_thrust
