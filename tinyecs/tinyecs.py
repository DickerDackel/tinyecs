"""The teeniest, tiniest ECS system

In contrast to other systems, I only give you an Entity class.  No
dedicated classes for components or systems/runners.

An Entity instance is basically nothing more than a list of components.

On creation, an entity is registered globally with each component it
contains.  New components that are added later are registered automatically
as well.

Also, the component is added as an attribute to the Entity object. So after
adding a 'name' component to a player, it can be accessed as player.name.

Once entities are created and components have been added to them, you call
the run_system method with a list of required components, the system
function, and a list of optional parameters.

Entities that are no longer needed can be removed from the registry by the
remove() method.
"""

eidx = {}
cidx = {}

class Entity:
    """This is the only class this system has.  Each object entity is an
    instance of this class.  The registry that maps entities to their
    components is a module global a.k.a. a singleton.  Yepp, we could pack this
    into its own ecs class and instantiate it, but fuck it!
    """

    def __init__(self, *components, tag=None):
        """Entity([(name, component, ...], [tag=None]) -> Entity object

            Create an Entity instance with optional components already added
            (see add() below for details).

            If you give the entity a tag (name), it can be queried by the
            entities method.  Even if you don't give it a tag, you can query it
            with 'None'.  Note, that multiple instances can have the same tag.

            Components are zero or more tuples containing the name and the
            actual component data.

                player = Entity(
                    ('name': 'Ze mighty'),
                    ('position', Vector(100, 42)),
                    tag='player')

                bullet = Entity(
                    ('lifetime', 50),
                    ('damage', 10),
                    ('position', Vector(50, 50)))

        """

        global eidx, cidx

        self.tag = tag

        # Register the entity by tag
        if tag not in eidx:
            eidx[tag] = []
        eidx[tag].append(self)

        # Add optionally passed components
        self.components = [self.add(name, comp) for name, comp in components]

    def add(self, name, component):
        """add(name, component) -> name

            Add a named component to an entity

                player.add('health', 100)

        """

        # Add component as full attribute addressable by name
        setattr(self, name, component)

        # add self to the list of entities that own this component
        if name not in cidx:
            cidx[name] = []
        cidx[name].append(self)

        return name

    def remove(self, component):
        """remove(component) -> None

        Remove a component from an entity.  This removes the actual component
        from the instance as well as from the component registry.
        """

        global cidx

        # Delete it from the info list
        self.components.remove(component)

        # Delete the class attribute
        del self.__dict__[component]

        # Delete the entity from the component's registry
        cidx[component].remove(self)

    def exit(self):
        """exit() -> None

            Removes the Entity instance from the registry.  If the registry is
            the only place that keeps a reference to the entity, the object
            will then automatically be deleted.

            Useful for objects with a lifetime that automatically delete
            themselves

                bullet.exit()

        """
        global eidx

        # Delete this entity from all components in the components registry use
        # 'list()' to create a copy, since remove() modifies self.components
        # while we're looping over it
        for c in list(self.components):
            self.remove(c)

        # Delete self from the Entity registry, also delete the slot for tag,
        # if no entities with that name are left.
        eidx[self.tag].remove(self)
        if len(eidx[self.tag]) == 0:
            del eidx[self.tag]

    def component(self, component):
        return getattr(self, component)

def entities_by_name(tag):
    """entities_by_name(tag) -> list of entities

    Returns a list of entities that match the tag

    Use this to access entities or their components outside systems.

        player = tinyecs.entities_by_tag('player')[0]
        bullets =tinyecs.entities_by_tag('projectiles')

    """

    try:
        return eidx[tag]
    except KeyError:
        return []

def run_system(fkt, conditions, *args, **kwargs):
    """run_system(fkt, conditions, *args, **kwargs) -> None

    Run fkt(entity, *components, *args, **kwargs) for all entities that contain all
    components listed in conditions.

    Note that components can only be changed, if they are complex types.
    An int() component will be passed by value and the change will never be
    reflected in the entity object.  In that case use 'entity.component'
    instead..  The semantics are the same as with normal function calls.

        def blast_damage_system(e, comps, bomb):
            health, position = comps
            if distance(e.position, bomb.position) < bomb.blast_radius:
                e.health -= bomb.damage

        player = Entity(('health', 100))

        def health_system(e, comps):
            # Change of health won't be transfered to e
            health, = comps
            if e.health <= 0:
                e.exit()

        bomb = Bomb(position=(100, 100), damage=42)
        Entity.run_system(blast_damage_system, ('health', 'position'), bomb)
        Entity.run_system(health_system, ('health',))

    """

    entities = [ set(grep(_)) for _ in conditions ]

    # Now logical-and all entities for every condition (a.k.a. component)
    # so we only get entities that contain all conditions.
    matching = entities[0]
    for e in entities[1:]:
        matching &= e

    for e in matching:
        components = [ e.component(_) for _ in conditions ]
        fkt(e, *components, *args, **kwargs)

def grep(component):
    """grep(name) -> list of entities

        Return a list of entities that own this component.  Use this to
        pass appropriate entities to the system/runner

            sprites_that_can_render = Entity.grep('has-sprite')

    """

    try:
        return cidx[component]
    except KeyError:
        return []
