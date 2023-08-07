"""Helpers for tinyecs

For tinyecs, see https://github.com/dickerdackel/tinyecs

Nothing in here couldn't be written yourself in a few minutes, it's just for
convenience.
"""

import pygame
import tinyecs as ecs

from functools import lru_cache
from pygame import Vector2


class ESprite(pygame.sprite.Sprite):
    """A sprite class especially for ECS entities.

    If an entity with a sprite component is removed, the sprite also needs to
    be removed from all sprite groups.

    `tinyecs` offers the `shutdown_` method for this.  If this is available,
    ecs.remove_entity will call it when tearing down an entity.

    Parameters
    ----------
    *groups : *pygame.sprite.Group()
        Directly passed into parent class.  See `pygame.sprite.Sprite` for
        details.

    tag : hashable = None
        A tag to identify this sprite.  Can e.g. be used for image caching.

    """
    def __init__(self, *groups, tag=None, image=None):
        super().__init__(*groups)

        if image is None:
            self.image = pygame.surface.Surface((1, 1))
        else:
            self.image = image

        self.rect = self.image.get_rect(bottomright=(-1, -1))

    def shutdown_(self):
        self.kill()


class EVSprite(pygame.sprite.Sprite):
    """A sprite class especially for ECS entities.

    The E stands for the ECS, the V for virtual sprite.

    If an entity with a sprite component is removed, the sprite also needs to
    be removed from all sprite groups.

    `tinyecs` offers the `shutdown_` method for this.  If this is available,
    ecs.remove_entity will call it when tearing down an entity.

    The "virtual" part of this entity is the image access.  The image is just
    a property that calls a factory function instead.  That way, image
    generation can be handed over to a different component.  The sprite itself
    is only responsible to provide a link to the sprite group, which handles
    the drawing.

    Parameters
    ----------
    image_factory: callable
        A zero parameter function that is expected to return a
        `pygame.surface.Surface` object.

    *groups: *pygame.sprite.Group()
        Directly passed into parent class.  See `pygame.sprite.Sprite` for
        details.

    """
    def __init__(self, image_factory, *groups):
        super().__init__(*groups)
        self.image_factory = image_factory

        self._image = pygame.surface.Surface((1, 1))
        self.rect = self._image.get_rect(bottomright=(-1, -1))

    def shutdown_(self):
        self.kill()

    @property
    def image(self):
        new_image = self.image_factory.image
        if new_image is self._image:
            return self._image
        else:
            self._image = new_image
            self.rect = self._image.get_rect(center=self.rect.center)

        return self._image

    @image.setter
    def image(self, image):
        raise RuntimeError('EVSprite.image is dynamically generated.')


class RSAImage:
    """A *R*otated, *S*caled and *A*lpha transparent image.

    Use this as a provider for an image in the `EVSprite` class, or with the
    combination of `ESprite` and `sprite_rsai_system`, all in the package
    `tinyecs.components`

    This class gets initialized with a base image.

    Every time, any of the attributes `rotation`, `scale` or `alpha` are written,
    an appropriate image is created from the base image.

    image creation is `functools.lru_cache`d.

    Parameters
    ----------
    image
        The base image.  Scaling and rotation is always done from this image to
        avoid incremental rounding errors in the image.

    rotation: float = 0
    scale: float = 1
    alpha: float = 255
        Initial rotation, scale, alpha

    Attributes
    ----------
    None

    Properties
    ----------
    image: pygame.Surface  (ro)

        The rotated/scaled/alpha transparent version of the base image

    rotation: float  (rw)
    scale: float  (rw)
    alpha: float  (rw)

        To get/set the appropriate properties of the image

    Raises
    ------
    RuntimeError when the image property is written

    """
    def __init__(self, image, rotation=0, scale=1, alpha=255):
        self._base_image = image

        # Only force image creation on the last property assignment.
        self._rotation = rotation
        self._scale = scale
        self.alpha = alpha

    @lru_cache(maxsize=1024)
    def _create(self, rotation, scale, alpha):
        image = pygame.transform.rotozoom(self._base_image, -self._rotation - 180, self._scale)
        image.set_alpha(self._alpha)
        return image

    def update(self):
        self._image = self._create(self.rotation, self.scale, self.alpha)

    @property
    def image(self):
        return self._image

    @property
    def rotation(self):
        return self._rotation

    @rotation.setter
    def rotation(self, phi):
        self._rotation = phi
        self.update()

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, scale):
        self._scale = scale
        self.update()

    @property
    def alpha(self):
        return self._alpha

    @alpha.setter
    def alpha(self, alpha):
        self._alpha = alpha
        self.update()


@dataclass
class LerpThing:
    """A generic gauge that lerps between 2 points.

    This class can be used for scaling, color shifts, momentum, ...

    It gets initialized with 2 Values for t0 and t1, and a time `interval`,
    then it lerps between these values.

    Once the interval has passed, depending on the `repeat` setting, the object
    will do one of the following:

        0: Don't repeat, just stop transmogrifying
        1: Reset and repeat from start
        2: Bounce back and forth

    Optionally, an easing function can be put on top of `t`.

    Parameters
    ----------
    v_t0,
    v_t1: [int | float]
        Values for t0 and t1

    ease: callable = lambda x: x
        An optional easing function to put over t

    interval: Cooldown
        The length of the lerp.  This duration is mapped onto the range 0 - 1
        as `t`.

    repeat: int = 0
        After the interval has finished, how to proceed?

            0: Don't repeat, just stop transmogrifying
            1: Reset and repeat from start
            2: Bounce back and forth.  Note, that bounce back is implemented by
               swapping v_t0 and v_t1.

    """
    value: float = field(init=False)
    v_t0: float = 0
    v_t1: float = 0
    ease: callable = lambda x: x
    repeat: int = 0
    interval: InitVar[Cooldown | float]

    def __post_init__(self, interval):
        self.value = self.v_t0
        self.interval = interval if isinstance(interval, Cooldown) else Cooldown(interval)

    def update(self):
        """Update the state of the LerpThing."""

        lerp = lambda a, b, t: (1 - t) * a + b * t

        if self.interval.cold and self.repeat:
            if self.repeat == 2:
                self.v_t0, self.v_t1 = self.v_t1, self.v_t0
            self.interval.reset()

        if self.interval.hot:
            t = self.interval.normalized
            self.value = lerp(self.v_t0, self.v_t1, self.ease(t))


def lerpthing_system(dt, eid, lerpthing):
    """Update a lerpthing through tinyecs."""

    lerpthing.update()


def dead_system(dt, eid, dead):
    """Reap entities marked with a `dead` component."""
    ecs.remove_entity(eid)


def deadzone_system(dt, eid, container, position):
    """Kill entities moving outside defined boundaries

    To avoid sprites flying off to infinity, a dead zone can be defined, that
    should be sufficiently larger than the screen.

    Entities entering that zone (or actually, leaving the container rect) will
    be removed.

    Parameters
    ----------
    container : pygame.rect.Rect
        The boundaries within entities stay alive.

    position : pygame.math.Vector2
        The location of the entity.

    Returns
    -------
    None

    """
    if not container.collidepoint(position):
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


def scale_system(dt, eid, scale, momentum):
    """Apply frictoin to a momentum.

    In contrast to a force, which adds a directional vector to the momentum,
    the friction scales the momentum by a factor.  It can also be greater 1.

    """
    momentum *= scale ** dt


friction_system = scale_system


def sprite_system(dt, eid, sprite, position):
    """Set the rect.center of sprite to position."""

    if sprite.rect:
        sprite.rect.center = position.xy
    else:
        sprite.rect = sprite.image.get_rect(center=position)


def wsad_system(dt, eid, wsad, position):
    """An example system to control a playear with the `wsad` keys.

    Given the following entity:

        e = ecs.create_entity()
        ecs.add_component(e, 'wsad', 250)  # pixels per second motion speed
        ecs.add_component(e, 'position', Vector2(x, y))
        ...

    running this system will modify the position component of the entity.

        ecs.run_system(dt, 'wsad', 'position', 'player')

    Parameters
    ----------
    wsad
        The speed in pixels per second to move when `wsad` are pressed.

    position
        The position component to change according to the key presses.

    """
    keys = pygame.key.get_pressed()

    v = Vector2()
    # Yes, I know, pep8...
    if keys[pygame.K_w]: v.y -= 1
    if keys[pygame.K_s]: v.y += 1
    if keys[pygame.K_a]: v.x -= 1
    if keys[pygame.K_d]: v.x += 1

    # Normalize so diagonals are not faster then axis motion
    if v: position += v.normalize() * wsad * dt
