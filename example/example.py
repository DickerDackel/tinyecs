import tinyecs as ecs


from dataclasses import dataclass

# Let's see, if the object will be destroyed if it's removed from the
# registry at the end
def destructor(self):
    print(f'Descructor of {self} called')
ecs.Entity.__del__ = destructor

@dataclass
class Position:
    x: float
    y: float

@dataclass
class Velocity:
    dx: float
    dy: float

ten_seconds_walker = ecs.Entity(
    ('name', '10 Seconds Walker'),
    ('position', Position(0, 0)),
    ('velocity', Velocity(0, 5)),
    ('lifetime', 10),
    ('printable', True),
    tag='Walker',
)

def motion_system(e, position, velocity, delta_time):
    # Note that assigning a new Vector to position would not make it back
    # into e.position.  But since we don't change the position instance
    # itself, we're safe.
    position.x += velocity.dx * delta_time
    position.y += velocity.dy * delta_time

def lifetime_system(e, lifetime, delta_time):
    # Note: lifetime is just an int and passed by value.  It cannot be
    #       modified.  e.lifetime must be used here.
    e.lifetime -= 1 * delta_time
    if e.lifetime <= 0:
        print(f'removing entity {e}')
        e.exit()

def render_system(e, printable):
    # the printable component contains no data at all and can be ignored,
    # but it will still be passed as a parameter.
    print(f'{e.name} has {e.lifetime} steps left, at {e.position}, walking towards {e.velocity}')

walker = ecs.entities_by_name('Walker')[0]
print('My walker object is ', ecs.entities_by_name('Walker'))
print('It has the following components');
print(walker.components)

ecs.run_system(render_system, ('printable'))
for i in range(15):
    ecs.run_system(motion_system, ('position', 'velocity'), 1)
    ecs.run_system(lifetime_system, ('lifetime',), 1)
    ecs.run_system(render_system, ('printable',))

