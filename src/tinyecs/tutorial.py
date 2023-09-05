'''
# tinyecs Tutorial

This tutorial is also available by running 

```sh
pydoc tinyecs.tutorial
```

The demo developed within this document can be run upfront with

```py
python -m tinyecs.tutorial
```

## About

ECS stands for Entity Component System, and it is a programming paradigm that
differs from the well known OO.

During my research I stumbled over

[this article series](https://t-machine.org/index.php/2007/09/03/entity-systems-are-the-future-of-mmog-development-part-1/)

and after reading part 2 and 3, I decided to implement an ECS myself, well
aware that `esper` is a solid and long existing implementation, but I wanted
to see how to implement it myself.

I'm not trying to sell you an ECS by explaining the problems of multiple
inheritance in game programming.  There are articles out there that do this in
much detail.  If you're here, you're already interested in the concept, so
this will be a tutorial, implementing a bunch of bouncing sprites, which
should show you all the API you need to know.

## Setting up the environment

I assume, you have a current version of python up & running on your computer
already, and you have a basic understanding of installing packages with `pip`.

I suggest to create a new project in a virtual environment, so your main
install stays clean from random dependency packages.  There are tutorials on
the web and on youtube how to do that on your platform, if you're unfamiliar
with the concept.

`tinyecs` itself is just a library to manage abstract entities.  It doesn't
rely on pygame-ce and could equally be used with other libs like `pyglet` or
even console applications like roguelikes.  It comes with a few preconfigured
components though, which were developed with pygame-ce, so this tutorial will
require to install that.

```sh
pip install pygame-ce
```

If you're runnning pygame already, I recommend to switch through new pygame
community edition, since most core developers migrated to this project.  This
tutorial will work with both `pygame-ce` and `pygame`, since it doesn't make
use of any updated features.

    Note: if anybody can tell me, how to depend on either pygame-ce or pygame,
    but be happy with whatever is already there in pyproject.toml, please tell
    me.

Next, of course you need tinyecs.  You're probably reading this tutorial after
cloning the project from github, or reading it directly on the site.

For completeness, the github project page is

    https://github.com/dickerdackel/tinyecs

The latest development version (unstable) can be installed from there with

```sh
pip install git+https://github.com/dickerdackel/tinyecs
```

Or you can install the stable version directly from pypi

```sh
pip install tinyecs
```

## The code

No, not yet.  First...

### ...Some concepts

To ease the code, I usually `import tinyecs as ecs`.  If you like to import it
in its normal namespace, please adapt all examples here accordingly.

#### Entities
An entity is just an identifyer for a "thing" in your world.  The examples
here will always call this `eid`.  It's role is about the same as an object in
game written in an object oriented style, e.g. a bonus coin.

In contrast to OO development, the entity is really just an ID.  Calling
`ecs.create_entity` will generate a random uuid4, but since entities are
actually keys into a dict internally, any hashable type will work too.  It
makes e.g. sense for the player entity to be quickly accessible by using
'player' as ID.

Entities are created and removed with

```py
eid = ecs.create_entity()  # gives you a uuid4 ID
player = ecs.create_entity('player')  # gives you 'player' as ID

ecs.remove_entity(eid)
```

If an entity is removed, all references to its components are also dropped, but...  See "IMPORTANT" below at "Components"

#### Components

To give life to this entity, "components" can be attached to it.  A component
is in its most basic form any data record.  Like a sprite, a position vector,
a record containing statistics like hitpoints or armor.

Components are addressed by a tag which is called `cid` (short for component
ID) during this tutorial.  Note, that there is also a component ID for the
actual object, but I have yet to find a use for that, and since `tag` is a
very general term, `cid` stuck with me and I always use it for this purpose.

Components are added and removed to and from an entity like this:

```py
ecs.add_component(eid, 'tag', object)

ecs.remove_component(eid, 'tag')
```

IMPORTANT:

An entity that e.g. has a sprite in a global sprite group cannot be released
by the ECS, since it doesn't know anything about the interface of that sprite.
The ECS and the sprite group are two different systems.

To deal with that issue, you can add a method `shutdown_` to your component,
which will be called when the component is removed from the ECS.

```py
# Remove a instance of a pygame.sprite.Sprite subclass
# from all sprite groups
def shutdown_(self):
    self.kill()
```

#### Systems

Different from writing OO, the component itself doesn't have any code (in the
purest form of ECS), which is where `systems` come into play.

A system is a function that works on a fixed set of components from a single
entity.  system functions are not called directly, but with the help of
tinyecs' `run_system` function.

Imagine a saucer entity, with the components `sprite`, `position`, and
`momentum`. It should appear on the screen at position (50, 50) and should fly
diagonally across the screen until it disappears off-screen.

```py
eid = ecs.create_entity()
ecs.add_component(eid, 'sprite', Sprite('saucer.jpg'))
ecs.add_component(eid, 'position', pygame.Vector2(50, 50))
ecs.add_component(eid, 'momentum', pygame.Vector2(1024, 768).normalized() * 100)
```

To apply the momentum to the position, a function `momentum_system` is needed.
To apply the position to the rect of the sprite, a function `sprite_system`
will be used.  To run e.g. the `momentum_system`, put the following into the
game loop:

``py
ecs.run_system(dt, momentum_system, 'momentum', 'position')
```

When the game loop passes this call, `run_system` will find all entities that
have both components `momentum` and `position` and pass these together with
deltatime `dt` and the entity ID into the `momentum_system` function.

Writing the `momentum_system` is easy:

```py
def momentum_system(dt, eid, momentum, position):
    position += momentum * dt
```

That's it.  Now every time run system is called for the `momentum_system`, all
objects with these two components will have their position updated.

Note:

If you need to put additional arguments from the game loop into the system,
use `**kwargs`.  `run_system` will pass all `cids` as `*args` into your custom
function, and all additional keyword args from the `run_system` call will
passed in after the components.  The following will be explained in the actual
script later.

```py
ecs.run_system(dt, deadzone_system, 'position', deadzone=WORLD)
```

So the system is basically the `update(dt)` function in an OO driven game.

At this point you might get the feeling, that you will have a very large list
of systems in a big block in your game loop, and that's exactly right.  You
either hate that, which is fine, so the option is either to go back to an OO
development model, or chose a more OO driven ECS implementation like e.g. the
long established `esper`.

There are some alternatives still.

1. you can register systems with the required cids at the start of your
program and call a single function in your game loop:

```py
ecs.run_all_systems(dt)
```

2. To give you a more fine grained control over what systems run together, the
concept of `domains` was introduced.  A system domain is simply a group of
systems that are bundled under a common name.  We won't make use of that in
this tutorial, please consult the embedded docs for more detail.

```sh
pydoc tinyecs.add_system_to_domain
pydoc tinyecs.run_domain
pydoc tinyecs.remove_system_from_domain
```

3. if you prefer to have normal classes as components and have the
functionality in there, just create a short system that calls the update
method of your component.  You still need that block of `run_system` or above
shortcuts in your game loop though.

```py
def call_update_system(dt, eid, component):
    component.update(dt)
```

### Finally code!

We now write a simple demo of colorful flying boxes.

If the user holds the mouse, a bunch of rectangular sprites of random size are
released at mouse position, drifting in random directions until the mouse is
released again.

Boxes that drift off screen will be automatically removed from the system.

tinyecs comes with a sprite that has a shutdown method, and also systems that
handle motion and screen boundaries, but we'll write these here ourselves, so
you get a feel for how things work.

####  A basic pygame game loop

This is a basic pygame boilerplate game loop.  It could be shortened, but this
is a good start for stateless test scripts and experiments.  It already has a
sprite group added.

```py
import pygame

TITLE = 'pygame minimal template'
SCREEN = pygame.Rect(0, 0, 1024, 768)
FPS = 60
DT_MAX = 3 / FPS

pygame.init()
pygame.display.set_caption(TITLE)
screen = pygame.display.set_mode(SCREEN.size)
clock = pygame.time.Clock()
group = pygame.sprite.Group()

running = True
while running:
    dt = min(clock.tick(FPS) / 1000.0, DT_MAX)

    for e in pygame.event.get():
        match e.type:
            case pygame.QUIT:
                running = False

            case pygame.KEYDOWN if e.key == pygame.K_ESCAPE:
                running = False

    screen.fill('black')

    ...
    group.update(dt)
    ...
    group.draw(screen)

    pygame.display.flip()
    runtime = pygame.time.get_ticks()/1000
    fps = clock.get_fps()

    pygame.display.set_caption(f'{TITLE} - {runtime=:.2f}  {fps=:.2f}')

pygame.quit()
```

#### The sprite class:

```py
from random import random, choice
from pygame.colordict import THECOLORS

class DemoSprite(pygame.sprite.Sprite):
    def __init__(self, *groups):
        # Make sure, the sprite is properly initialized for sprite groups
        super().__init__(*groups)

        # Size is random between 8 and 32 pixels in both dimensions
        w, h = random() * 24 + 8, random() * 24 + 8

        # Just set up a basic pygame sprite instance
        self.image = pygame.Surface((w, h))
        self.image.fill(choice(list(THECOLORS)))

        # Note that we don't set the position!
        self.rect = self.image.get_rect()

    def shutdown_(self):
        print(f'{self} removed from sprite groups')
        self.kill()
```

#### Creating an entity

We define a function that creates the full entity.  If you're coming from OO,
this mostly resembles the `__init__` of an entity class.

```py
from pygame import Vector2

def create_box_entity(position):
    # Give sprites a random speed between 0 and +/-50px/s
    dx, dy = random() * 100 - 50, random() * 100 - 50

    e = ecs.create_entity()
    ecs.add_component(e, 'position', Vector2(position))
    ecs.add_component(e, 'momentum', Vector2(dx, dy))
    ecs.add_component(e, 'sprite', DemoSprite)
```

This function will be called if the mouse button is pressed to generate a
spray of new sprites at the given mouse position.

#### The systems

We already wrote the `momentum_system` above, but here again for completeness:

```py
# Make the world rect a bit larger than the screen, so sprites don't suddenly
# disappear at the screen edge.  Note: rect.scale_by is a pygame-ce
# addition.
WORLD = SCREEN.scale_by(1.25)

def momentum_system(dt, eid, momentum, position):
    """Add a delta time scaled momentum to the position."""
    position += momentum * dt

def sprite_position_system(dt, eid, sprite, position):
    """Apply the position to the rect of the sprite for the sprite group"""
    sprite.rect.center = position

def deadzone_system(dt, eid, position, *, world):
    """Kill sprites that move off screen"""
    if world.collidepoint(position):
        return
    ecs.remove_entity(eid)
```

#### Releasing entities on click

The lines marked with `>` are additions to the game loop template all above.

```py
>   emitting = False
    running = True
    while running:
        dt = min(clock.tick(FPS) / 1000.0, DT_MAX)

        for e in pygame.event.get():
            match e.type:
                case pygame.QUIT:
                    running = False

>               case pygame.MOUSEBUTTONDOWN if e.button == 1:
>                   emitting = True

>               case pygame.MOUSEBUTTONUP if e.button == 1:
>                   emitting = False

                case pygame.KEYDOWN if e.key == pygame.K_ESCAPE:
                    running = False

>       if emitting: 
>           for _ in range(10):
>               create_box_entity(pygame.mouse.get_pos())

        screen.fill('black')
```

#### Running the systems

```py
>   ecs.run_system(dt, momentum_system, 'momentum', 'position')
>   ecs.run_system(dt, deadzone_system, 'position', world=WORLD)
>   ecs.run_system(dt, sprite_position_system, 'sprite', 'position')

    screen.fill('black')

>   # group.update(dt)  # Not needed
    group.draw(screen)

    pygame.display.flip()

```

#### That's it.

Here's the full script with the functions, classes, imports above also merged
in.  Additionally, a sprite counter was added to the title bar and the print
from the `shutdown_` of the sprite class was commented out.

```py
import pygame
import tinyecs as ecs

from random import random, choice

from pygame import Vector2
from pygame.colordict import THECOLORS

TITLE = 'pygame minimal template'
SCREEN = pygame.Rect(0, 0, 1024, 768)
FPS = 60
DT_MAX = 3 / FPS

# Make the world rect a bit larger than the screen, so sprites don't suddenly
# disappear at the screen edge.  Note: rect.scale_by is a pygame-ce
# addition.
WORLD = SCREEN.scale_by(1.25)


class DemoSprite(pygame.sprite.Sprite):
    def __init__(self, *groups):
        # Make sure, the sprite is properly initialized for sprite groups
        super().__init__(*groups)

        # Size is random between 8 and 32 pixels in both dimensions
        w, h = random() * 24 + 8, random() * 24 + 8

        # Just set up a basic pygame sprite instance
        self.image = pygame.Surface((w, h))
        self.image.fill(choice(list(THECOLORS)))

        # Note that we don't set the position!
        self.rect = self.image.get_rect()

    def shutdown_(self):
        # print(f'{self} removed from sprite groups')
        self.kill()


def create_box_entity(position, sprite_group):
    # Give sprites a random speed between 0 and +/-50px/s
    dx, dy = random() * 100 - 50, random() * 100 - 50

    e = ecs.create_entity()
    ecs.add_component(e, 'position', Vector2(position))
    ecs.add_component(e, 'momentum', Vector2(dx, dy))
    ecs.add_component(e, 'sprite', DemoSprite(sprite_group))


def momentum_system(dt, eid, momentum, position):
    """Add a delta time scaled momentum to the position."""
    position += momentum * dt


def sprite_position_system(dt, eid, sprite, position):
    """Apply the position to the rect of the sprite for the sprite group"""
    sprite.rect.center = position


def deadzone_system(dt, eid, position, *, world):
    """Kill sprites that move off screen"""
    if world.collidepoint(position):
        return
    ecs.remove_entity(eid)


pygame.init()
pygame.display.set_caption(TITLE)
screen = pygame.display.set_mode(SCREEN.size)
clock = pygame.time.Clock()
group = pygame.sprite.Group()

emitting = False
running = True
while running:
    dt = min(clock.tick(FPS) / 1000.0, DT_MAX)

    for e in pygame.event.get():
        match e.type:
            case pygame.QUIT:
                running = False

            case pygame.MOUSEBUTTONDOWN if e.button == 1:
                emitting = True

            case pygame.MOUSEBUTTONUP if e.button == 1:
                emitting = False

            case pygame.KEYDOWN if e.key == pygame.K_ESCAPE:
                running = False

    if emitting:
        for _ in range(10):
            create_box_entity(pygame.mouse.get_pos(), group)

    ecs.run_system(dt, momentum_system, 'momentum', 'position')
    ecs.run_system(dt, deadzone_system, 'position', world=WORLD)
    ecs.run_system(dt, sprite_position_system, 'sprite', 'position')

    screen.fill('black')

    group.draw(screen)

    pygame.display.flip()
    runtime = pygame.time.get_ticks() / 1000
    fps = clock.get_fps()
    sprites = len(group)

    pygame.display.set_caption(f'{TITLE} - {runtime=:.2f}  {fps=:.2f}  {sprites=}')

pygame.quit()
```

## Available components and systems

Now that we've written 3 basic systems ourself, let's have a look at the
pygame(-ce) components that are currently included with tinyecs.

Please note that while tinyecs should be API stable by now, the bundled
components in `tinyecs.compsys` are *not*.  I'm still trying to get a feel for
some of the features I want and how I want to access them.

Components and systems are only listed here.  Please check the embedded docs
for details and look at the code to decide if you want to make use of these
systems or if you'd rather roll your own.

I usually import these together with tinyecs like this:

```sh
import tinyecs as ecs
import tinyecs.compsys as ecsc
```


`class ESprite(pygame.sprite.Sprite)`:
    A sprite class that already has a `shutdown_` method

`class EVSprite(pygame.sprite.Sprite)`:
    A sprite class where the image attribute is a property.  You can pass an
    `image_factory` function to the init that will generate images when the
    `group.draw` functions runs over it.

`class RSAImage`:
    A *R*otated, *S*caled and *A*lpha transparent image.

    UNSTABLE!  DON'T RELY ON THIS YET!

`def dead_system(dt, eid, dead)`:
    Sometimes it is useful to not remove a sprite immediately from the system.
    Instead, you can add a component tagged e.g. 'dead', and later reap all
    entities marked with that tag.

`def deadzone_system(dt, eid, world, position, *, container)`:

    Basically the function created in this tutorial, with one addition.

    Not every sprite is run through this system, only sprites that have a
    `world` component.  That way, e.g. enemy sprites waiting off screen to be
    activated will not get removed.

    `world` can be anything, I usually make it a boolean, but the existence of
    that component alone is sufficient.

        ecs.add_component(e, 'world', True)

`def extension_system(dt, eid, extension)`:
    Will be removed.  tinyecs installs pgcooldown as a requirement and that
    comes with the `CronD` class which does the same and more.

`def force_system(dt, eid, force, momentum)`:
    Applies (adds) a constant force to a momentum.

`def lifetime_system(dt, eid, lifetime)`:
    Kills the entity once lifetime has run out.  Expects `lifetime` to be an
    instance of `pgcooldown.Cooldown`

`def momentum_system(dt, eid, momentum, position)`:
    The same as we wrote in the tutorial above.

`def mouse_system(dt, eid, mouse, position)`:
    Update a position component with the position of the mouse cursor.

`def scale_system(dt, eid, scale, momentum)`:
`def friction_system(dt, eid, scale, momentum)`:
    Apply friction to a momentum.

    In contrast to a force_system, which adds a directional vector to the
    momentum, the friction scales the momentum by a factor.  It can also be
    greater 1.

    `friction_system` is an alias to `scale_system`.

`def sprite_system(dt, eid, sprite, position)`:
    The same as we wrote above, apply the position to `sprite.rect.center`.

`def wsad_system(dt, eid, wsad, position)`:
    An example system to control a playear with the `wsad` keys.
    This was just a proof of concept, but I'm currently using it, so perhaps
    it will stay.
'''

import pygame
import tinyecs as ecs

from random import random, choice

from pygame import Vector2
from pygame.colordict import THECOLORS

TITLE = 'pygame minimal template'
SCREEN = pygame.Rect(0, 0, 1024, 768)
FPS = 60
DT_MAX = 3 / FPS

# Make the world rect a bit larger than the screen, so sprites don't suddenly
# disappear at the screen edge.  Note: rect.scale_by is a pygame-ce
# addition.
WORLD = SCREEN.scale_by(1.25)


class DemoSprite(pygame.sprite.Sprite):
    """Just a class that provides a basic image and the shutdown_ method"""
    def __init__(self, *groups):
        # Make sure, the sprite is properly initialized for sprite groups
        super().__init__(*groups)

        # Size is random between 8 and 32 pixels in both dimensions
        w, h = random() * 24 + 8, random() * 24 + 8

        # Just set up a basic pygame sprite instance
        self.image = pygame.Surface((w, h))
        self.image.fill(choice(list(THECOLORS)))

        # Note that we don't set the position!
        self.rect = self.image.get_rect()

    def shutdown_(self):
        # print(f'{self} removed from sprite groups')
        self.kill()


def create_box_entity(position, sprite_group):
    """Create an entity with position, momentum and sprite components."""
    # Give sprites a random speed between 0 and +/-50px/s
    dx, dy = random() * 100 - 50, random() * 100 - 50

    e = ecs.create_entity()
    ecs.add_component(e, 'position', Vector2(position))
    ecs.add_component(e, 'momentum', Vector2(dx, dy))
    ecs.add_component(e, 'sprite', DemoSprite(sprite_group))


def momentum_system(dt, eid, momentum, position):
    """Add a delta time scaled momentum to the position."""
    position += momentum * dt


def sprite_position_system(dt, eid, sprite, position):
    """Apply the position to the rect of the sprite for the sprite group"""
    sprite.rect.center = position


def deadzone_system(dt, eid, position, *, world):
    """Kill sprites that move off screen"""
    if world.collidepoint(position):
        return
    ecs.remove_entity(eid)


def main():
    pygame.init()
    pygame.display.set_caption(TITLE)
    screen = pygame.display.set_mode(SCREEN.size)
    clock = pygame.time.Clock()
    group = pygame.sprite.Group()

    emitting = False
    running = True
    while running:
        dt = min(clock.tick(FPS) / 1000.0, DT_MAX)

        for e in pygame.event.get():
            match e.type:
                case pygame.QUIT:
                    running = False

                case pygame.MOUSEBUTTONDOWN if e.button == 1:
                    emitting = True

                case pygame.MOUSEBUTTONUP if e.button == 1:
                    emitting = False

                case pygame.KEYDOWN if e.key == pygame.K_ESCAPE:
                    running = False

        if emitting:
            for _ in range(10):
                create_box_entity(pygame.mouse.get_pos(), group)

        ecs.run_system(dt, momentum_system, 'momentum', 'position')
        ecs.run_system(dt, deadzone_system, 'position', world=WORLD)
        ecs.run_system(dt, sprite_position_system, 'sprite', 'position')

        screen.fill('black')

        group.draw(screen)

        pygame.display.flip()
        runtime = pygame.time.get_ticks() / 1000
        fps = clock.get_fps()
        sprites = len(group)

        pygame.display.set_caption(f'{TITLE} - {runtime=:.2f}  {fps=:.2f}  {sprites=}')

    pygame.quit()


if __name__ == "__main__":
    main()
