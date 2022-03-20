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

class Entity:
    """This is the only class this system has.  Each object entity is an
    instance of this class.  The registry that maps entities to their
    components is a class global a.k.a. a singleton.
    """

    cidx = {}

    def __init__(self, *components):
        """Entity([(name, component, ...]) -> Entity object

            Create an Entity instance with optional components already added
            (see add() below for details).

            components are zero or more tuples containing the name and the
            actual component data.

                player = Entity(
                    ('name': 'Ze mighty'),
                    ('position', Vector(100, 42)))

        """

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
        if name not in self.cidx:
            self.cidx[name] = []
        self.cidx[name].append(self)

        return name

    def remove(self):
        """remove() -> None

            Removes the Entity instance from the registry

            Useful for objects with a lifetime that automatically delete
            themselves

                bullet.remove()

        """

        for i in self.components:
            self.cidx[i].remove(self)

    @classmethod
    def grep(cls, component):
        """grep(name) -> list of entities

            Return a list of entities that own this component.  Use this to
            pass appropriate entities to the system/runner

                sprites_that_can_render = Entity.grep('has-sprite')

        """

        try:
            return cls.cidx[component]
        except KeyError:
            return []

    @classmethod
    def run_system(cls, conditions, fkt, *args, **kwargs):
        """run_system(conditions, fkt, *args, **kwargs) -> None

        Run fkt(entity, *args, **kwargs) for all entities that contain all
        components listed in conditions.

            def blast_damage_system(e, bomb):
                if distance(e.position, bomb.position) < bomb.blast_radius:
                    e.health -= bomb.damage

            def health_system(e):
                if e.health <= 0:
                    e.remove()

            bomb = Bomb(position=(100, 100), damage=42)
            Entity.run_system(('health', 'position'), blast_damage_system, bomb)
            Entity.run_system(('health'), health_system)

        """

        entities = [set(cls.grep(_)) for _ in conditions]

        matching = entities[0]
        for e in entities[1:]:
            matching &= e

        for e in matching:
            fkt(e, *args, **kwargs)


if __name__ == '__main__':
    from dataclasses import dataclass

    @dataclass
    class Position:
        x: float
        y: float

    @dataclass
    class Velocity:
        dx: float
        dy: float

    ten_seconds_walker = Entity(
        ('name', '10 Seconds Walker'),
        ('position', Position(0, 0)),
        ('velocity', Velocity(0, 5)),
        ('lifetime', 10),
        ('printable', True),
    )

    def motion_system(e, delta_time):
        e.position.x += e.velocity.dx * delta_time
        e.position.y += e.velocity.dy * delta_time

    def lifetime_system(e, delta_time):
        e.lifetime -= 1 * delta_time
        if e.lifetime <= 0:
            print(f'removing entity {e.name}')
            e.remove()

    def render_system(e):
        print(f'{e.name} has {e.lifetime} steps left, at {e.position}, walking towards {e.velocity}')

    Entity.run_system(('printable'), render_system)
    for i in range(15):
        Entity.run_system(('position', 'velocity'), motion_system, 1)
        Entity.run_system(('lifetime',), lifetime_system, 1)
        Entity.run_system(('printable',), render_system)
