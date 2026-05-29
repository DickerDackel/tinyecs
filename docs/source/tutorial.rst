tinyecs Tutorial
################

This tutorial is also available by running::

    pydoc tinyecs.tutorial

The demo developed within this document can be run upfront with::

    python -m tinyecs.tutorial

Setting up the environment
==========================

I assume, you have a current version of python up & running on your computer
already, and you have a basic understanding of installing packages with
``pip``.

I suggest to create a new project in a virtual environment, so your main
install stays clean from random dependency packages.  There are tutorials on
the web and on youtube how to do that on your platform, if you're unfamiliar
with the concept.

``tinyecs`` itself is just a library to manage abstract entities.  It doesn't
rely on :term:`pygame-ce` and could equally be used with other libs like
`pyglet <https://pyglet.org/>`_ or even console applications like roguelikes.
For this tutorial, we'll use pygame-ce though::

    pip install pygame-ce

Next, of course you need `tinyecs <https://github.com/dickerdackel/tinyecs>`_.
You're probably reading this tutorial after cloning the project from github,
or reading it directly on the site.

The latest development version (unstable) can be installed from there with::

    pip install git+https://github.com/dickerdackel/tinyecs

Or you can install the stable version directly from pypi::

    pip install tinyecs

This is the full preparation on Linux (and probably Mac)::

   mkdir tinyecs-tutorial
   cd tinyecs-tutorial
   python3 -m venv --prompt tinyecs-tutorial .venv
   source .venv/bin/activate
   python3 -m pip install pygame-ce
   python3 -m pip install tinyecs

...and to the best of my knowledge, if you have installed python properly,
this should work on Windows::

   md tinyecs-tutorial
   cd tinyecs-tutorial
   py -m venv --prompt tinyecs-tutorial .venv
   .venv/bin/activate.bat
   py -m pip install pygame-ce
   py -m pip install tinyecs

The code
========

No, not yet.  First...

...Some concepts
----------------

To ease the code, I usually ``import tinyecs as ecs``.  If you like to
import it in its normal namespace, please adapt all examples here accordingly.

Entities
--------

An :term:`Entity` is just an identifyer for a "thing" in your world.  The
examples here will always call this ``eid``.  It's role is about the same as
an object in game written in an object oriented style, e.g. a bonus coin.

In contrast to OO development, the entity is really just an ID.  Calling
:py:func:`ecs.create_entity <tinyecs.create_entity>` will generate a random uuid4, but since entities are
actually keys into a dict internally, any hashable type will work too.  It
makes e.g. sense for the player entity to be quickly accessible by using
``"player"`` as ID.

Entities are created and removed with::

    eid = ecs.create_entity()  # gives you a uuid4 ID
    player = ecs.create_entity('player')  # gives you 'player' as ID
    ...
    ecs.remove_entity(eid)

If an entity is removed, all references to its components are also dropped,
but...  See :ref:`IMPORTANT <IMPORTANT>` below.

Components
----------

To give life to this entity, "components" can be attached to it.  A
:term:`Component` is in its most basic form any data record.  Like a sprite, a
position vector, a record containing statistics like hitpoints or armor.

Components are addressed by a :term:`ComponentID`, which is like the
:term:`EntityID` just anything you can use as key in a ``dict``.  I refer to
component IDs as ``cid`` throughout this document and in pretty much all my
code using tinyecs.

Components are added and removed to and from an entity like this::

    ecs.add_component(eid, 'tag', object)
    ...
    ecs.remove_component(eid, 'tag')

.. _IMPORTANT:

.. important::

    A component might have references in structures outside the ECS.  Like e.g.
    you can put a ``pygame`` sprite into a sprite group.  If the entity is killed,
    all references to the component **inside the ECS** will be removed, but the
    ECS does not know about the sprite group, so the entity will be killed, but
    there's still the refernce inside the sprite group.

    To deal with that issue, you can add a method ``shutdown_`` to your component,
    which will be called when the component is removed from the ECS::

        # Remove a instance of a pygame.sprite.Sprite subclass
        # from all sprite groups
        def shutdown_(self):
            self.kill()

Properties
----------

:term:`Properties <Property>` are a new addition to tinyecs.  Until now, the
only way to mark an entity to be of a specific type, or have a special
feature, was to add a flag component, e.g.::

    ecs.add_component(eid, 'is-drawable', True)

while not pretty, this does the job, but has the problem that you now need
different systems for times when you do want to filter, and if you don't want
to, since that flag component is added to the arguments of the system.

To solve this, properties (as inspired by Lisp) have been added.  These are
"flags" that live outside the component registry.  They will **not** be handed
over to the system when used in ``run_system``.

You can add, remove, and check for them like this::

    ecs.set_property(eid, 'is-drawable')
    ecs.has_property(eid, 'is-drawable')  # --> True
    ecs.remove_property(eid, 'is-drawable')

The tinyecs functions that return multiple entities and components now support
filtering by these properties.::

    ecs.run_system(dt, 'position', 'sprite', has_properties={'is-drawable'})

    ecs.has(eid, has_properties={'is-sprite'})

    entities = ecs.eids_by_cids('position', 'sprite', has_properties={'is-drawable'})

    components = ecs.comps_of_archetype('position', 'sprite', has_properties={'is-drawable', ...})

This way, e.g. sprites can now be layered by filtering for the different
types::

    ecs.run_system(0, render_sprites, 'position', 'sprite', has_properties={'is-enemy'})
    ecs.run_system(0, render_sprites, 'position', 'sprite', has_properties={'is-bullet'})
    ecs.run_system(0, render_sprites, 'position', 'sprite', has_properties={'is-fx'})
    ecs.run_system(0, render_sprites, 'position', 'sprite', has_properties={'is-hud'})

Finally, properties can be searched directly, e.g. to prune dead entities::

    for eid in ecs.eid_by_property('is-dead'):
        ecs.remove_entity(eid)

Systems
-------

Different from writing OO, the component itself doesn't have any code (in the
purest form of ECS), which is where *systems* come into play.

A system is a function that works on a fixed set of components from a single
entity.  System functions are not called directly, but with the help of
tinyecs' ``run_system`` function.

Imagine a saucer entity, with the components ``sprite``, ``position``, and
``momentum``. It should appear on the screen at position (50, 50) and should fly
diagonally across the screen until it disappears off-screen.::

    eid = ecs.create_entity()
    ecs.add_component(eid, 'sprite', Sprite('saucer.jpg'))
    ecs.add_component(eid, 'position', pygame.Vector2(50, 50))
    ecs.add_component(eid, 'momentum', pygame.Vector2(1024, 768).normalized() * 100)

To apply the momentum to the position, a function ``momentum_system`` is needed.
To apply the position to the rect of the sprite, a function ``sprite_system``
will be used.  To run e.g. the ``momentum_system``, put the following into the
game loop::

    ecs.run_system(dt, momentum_system, 'momentum', 'position')

When the game loop passes this call, ``run_system`` will find all entities that
have both components ``momentum`` and ``position`` and pass these together with
deltatime ``dt`` and the entity ID into the ``momentum_system`` function.

Writing the ``momentum_system`` is easy::

    def momentum_system(dt, eid, momentum, position):
        position += momentum * dt

That's it.  Now every time run system is called for the ``momentum_system``, all
objects with these two components will have their position updated.

.. note::

    If you need to put additional arguments from the game loop into the system,
    use ``**kwargs``.  ``run_system`` will pass all ``cids`` as ``*args`` into your custom
    function, and all additional keyword args from the ``run_system`` call will
    passed in after the components.  The following will be explained in the actual
    script later.::

        ecs.run_system(dt, deadzone_system, 'position', deadzone=WORLD)

So the system is basically the ``update(dt)`` function in an OO driven game.

At this point you might get the feeling, that you will have a very large list
of systems in a big block in your game loop, and that's exactly right.  You
either hate that, which is fine, so the option is either to go back to an OO
development model, or chose a more OO driven ECS implementation like e.g. the
long established `esper <https://github.com/benmoran56/esper>`_.

There are some alternatives still.

1. you can register systems with the required cids at the start of your
   program and call a single function in your game loop::

        ecs.run_all_systems(dt)

2. To give you a more fine grained control over what systems run together, the
   concept of ``domains`` was introduced.  A system domain is simply a group of
   systems that are bundled under a common name.  We won't make use of that in
   this tutorial, please consult the :ref:`API docs <api-bulk-run>` for more detail.

   * :py:func:`tinyecs.add_system_to_domain`
   * :py:func:`tinyecs.add_system_to_domain`
   * :py:func:`tinyecs.run_domain`
   * :py:func:`tinyecs.remove_system_from_domain`

3. If you prefer to have normal classes as components, or you have OO classes
   in your toolkit that you want to keep using, just create a short system
   that calls the update method of your component.

   .. code-block:: python

        def call_update_system(dt, eid, component):
            component.update(dt)

   .. note::

       If your OO class needs other parameters, you might run into access issues,
       because tinyecs doesn't know anything about which runtime arguments your
       method needs.  You might have a thorough look at your existing code base
       or design to see, if this will be an issue.

Finally code!
=============

We now write a simple demo of colorful flying boxes.

If the user holds the mouse, a bunch of rectangular sprites of random size are
released at mouse position, drifting in random directions until the mouse is
released again.

Boxes that drift off screen will be automatically removed from the system.

tinyecs comes with a sprite that has a shutdown method, and also systems that
handle motion and screen boundaries, but we'll write these here ourselves, so
you get a feel for how things work.

A basic pygame game loop
------------------------

This is a basic pygame boilerplate game loop.  It could be shortened, but this
is a good start for stateless test scripts and experiments.  It already has a
sprite group added.

.. code-block::

    import pygame

    TITLE = 'tinyecs tutorial'
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

The sprite class
----------------

.. code-block::

    from random import random, choice
    from pygame.colordict import THECOLORS

    class DemoSprite(pygame.sprite.Sprite):
        def __init__(self, *groups):
            # Make sure, the sprite is properly initialized for sprite groups
            super().__init__(*groups)

            # Create a rectangle surface of 8-32 pixels on each side, filled with
            # a random color.
            w, h = random() * 24 + 8, random() * 24 + 8
            self.image = pygame.Surface((w, h))
            self.image.fill(choice(list(THECOLORS)))

            # Note that we don't position that rect!
            self.rect = self.image.get_rect()

        def shutdown_(self):
            print(f'{self} removed from sprite groups')
            self.kill()

Creating an entity
------------------

We define a function that creates the full entity.  If you're coming from OO,
this mostly resembles the ``__init__`` of an entity class.

.. code-block::

    from pygame import Vector2

    def create_box_entity(position, sprite_group):
        # Give sprites a random speed between 0 and +/-50px/s
        dx, dy = random() * 100 - 50, random() * 100 - 50

        e = ecs.create_entity()
        ecs.add_component(e, 'position', Vector2(position))
        ecs.add_component(e, 'momentum', Vector2(dx, dy))
        ecs.add_component(e, 'sprite', DemoSprite(sprite_group))

This function will be called if the mouse button is pressed to generate a
spray of new sprites at the given mouse position.

The systems
-----------

We already wrote the ``momentum_system`` above, but I'll put it here again for
completeness:

.. code-block::

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

.. note::

   A bit about how components are stored, and what the implication of that is:

   Under the hood, components are stored in a dict.  When the system is
   called, usually a reference to that dict entry is passed to the system function.

   You can now modify attributes of that component.  What you can not do, is
   just assigning a new value to the component itself, since you only got a
   reference to it.  That means you would replace the component within the
   scope of the system function, but the component in the registry would still
   be unchanged.

   If you need to actually replace the component, e.g. if it's an immutable
   object that's passed by value instead of reference, you need to re-add it
   to the entity instead of overwriting the component variable.

   .. code-block::

      def take_damage_system(dt, eid, health, damage):
          ecs.add_component(eid, 'health', health - damage)

   For semantic reasons, tinyecs also provides ``update_component``, but that's
   literally an alias to the ``add_component`` function.

Releasing entities on click
---------------------------

The lines marked with ``>`` are additions to the game loop template all above.

.. code-block::

        running = True
        while running:
            dt = min(clock.tick(FPS) / 1000.0, DT_MAX)

            for e in pygame.event.get():
                match e.type:
                    case pygame.QUIT:
                        running = False
                    case pygame.KEYDOWN if e.key == pygame.K_ESCAPE:
                        running = False

    >       if pygame.mouse.get_pressed()[0]:
    >           pos = pygame.mouse.get_pos()
    >           for _ in range(10):
    >               create_box_entity(pos, group)

            screen.fill('black')

Running the systems
-------------------

.. code-block::

        if pygame.mouse.get_pressed()[0]:
            for _ in range(10):
                pos = pygame.mouse.get_pos()
                create_box_entity(pos, group)

    >   ecs.run_system(dt, momentum_system, 'momentum', 'position')
    >   ecs.run_system(dt, deadzone_system, 'position', world=WORLD)
    >   ecs.run_system(dt, sprite_position_system, 'sprite', 'position')

        screen.fill('black')

    >   # group.update(dt)  # Not needed, taken care by the systems
        group.draw(screen)

        pygame.display.flip()

That's it
---------

Here's the full script with the functions, classes, imports above also merged
in.  Additionally, a sprite counter was added to the title bar and the print
from the ``shutdown_`` of the sprite class was commented out.

.. code-block::

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

    running = True
    while running:
        dt = min(clock.tick(FPS) / 1000.0, DT_MAX)

        for e in pygame.event.get():
            match e.type:
                case pygame.QUIT:
                    running = False
                case pygame.KEYDOWN if e.key == pygame.K_ESCAPE:
                    running = False

        if pygame.mouse.get_pressed()[0]:
            for _ in range(10):
                pos = pygame.mouse.get_pos()
                create_box_entity(pos, group)

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

Available components and systems
================================

.. note::

    In the beginning, I created a set of pre-made components and systems, but
    I kept redesigning them again and again and am not using those anymore,
    since they are far to specific and tying the use of tinyecs to pygame-ce.

    There might be dedicated packages in the future, or not.  I'll leave those
    old components as examples in, but they're unsupported and not intended to
    be used.
