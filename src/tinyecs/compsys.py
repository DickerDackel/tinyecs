"""Helpers for tinyecs

For tinyecs, see https://github.com/dickerdackel/tinyecs

Nothing in here couldn't be written yourself in a few minutes, it's just for
convenience.
"""

import pygame
import tinyecs as ecs

from pygame import Vector2

__all__ = ["ESprite", "EVSprite", "RSAImage", "dead_system",
           "deadzone_system", "extension_system", "force_system",
           "lifetime_system", "momentum_system", "mouse_system",
           "scale_system", "friction_system", "sprite_system", "wsad_system"]


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

    Every time, any of the attributes `rotate`, `scale` or `alpha` are written,
    an appropriate image is created from the base image.

    image creation is `functools.lru_cache`d.

    Parameters
    ----------
    image
        The base image.  Scaling and rotation is always done from this image to
        avoid incremental rounding errors in the image.

    rotate: float = 0
    scale: float = 1
    alpha: float = 255
        Initial rotation, scaling, alpha

    Attributes
    ----------
    None

    Properties
    ----------
    image: pygame.Surface  (ro)

        The rotated/scaled/alpha transparent version of the base image

    rotate: float  (rw)
    scale: float  (rw)
    alpha: float  (rw)

        To get/set the appropriate properties of the image

    Raises
    ------
    RuntimeError when the image property is written

    """
    def __init__(self, image, rotate=0, scale=1, alpha=255, image_factory=None):
        self._base_image = self._image = image
        self.image_factory = image_factory

        self.locked = True
        self.rotate = rotate
        self.scale = scale
        self.alpha = alpha
        self.locked = False
        if self._image is None:
            raise RuntimeError('huh?')

    def __repr__(self):
        return f'{__class__}(image={self._base_image}, rotate={self._rotate}, scale={self._scale}, alpha={self._alpha}, locked={self._locked}, image_factory={self.image_factory})'

    @property
    def locked(self):
        return self._locked

    @locked.setter
    def locked(self, lck):
        self._locked = lck
        if not lck:
            self.update()

    # @lru_cache(maxsize=1024)
    def _create(self, rotate, scale, alpha):
        if self.image_factory:
            image = self.image_factory(rotate=int(self._rotate),
                                       scale=round(self._scale, 2),
                                       alpha=int(self._alpha))
        else:
            image = pygame.transform.rotozoom(self._base_image,
                                              self._rotate,
                                              self._scale)
            image.set_alpha(self._alpha)
        return image

    def update(self):
        # This needs to be called indirectly, with the parameter set, so
        # lru_cache can do its thing.
        if not self.locked:
            self._image = self._create(self.rotate, self.scale, self.alpha)

    def __call__(self, *args, **kwargs):
        return self._image

    @property
    def image(self):
        return self._image

    @property
    def rotate(self):
        return self._rotate

    @rotate.setter
    def rotate(self, phi):
        self._rotate = phi
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
