import tinyecs as ecs

from enum import Enum, auto
from dataclasses import dataclass
from types import SimpleNamespace


class Comps(Enum):
    NAME = auto()
    POSITION = auto()
    VELOCITY = auto()
    LIFETIME = auto()
    PRINTABLE = auto()


@dataclass
class Position:
    x: float
    y: float


@dataclass
class Velocity:
    dx: float
    dy: float


ten_seconds_walker = ecs.create_entity(tag='Walker')
ecs.add_component(ten_seconds_walker, Comps.NAME, '10 Seconds Walker')
ecs.add_component(ten_seconds_walker, Comps.POSITION, Position(0, 0))
ecs.add_component(ten_seconds_walker, Comps.VELOCITY, Velocity(0, 5))
ecs.add_component(ten_seconds_walker, Comps.LIFETIME, SimpleNamespace(time_left=10))
ecs.add_component(ten_seconds_walker, Comps.PRINTABLE, True)


def motion_system(dt, eid, position, velocity):
    # Note that assigning a new Vector to position would not make it back
    # into e.position.  But since we don't change the position instance
    # itself, we're safe.
    position.x += velocity.dx * dt
    position.y += velocity.dy * dt


def lifetime_system(dt, eid, lifetime):
    lifetime.time_left -= 1 * dt
    if lifetime.time_left <= 0:
        print(f'removing entity {eid}')
        ecs.remove_entity(eid)


def render_system(dt, eid, printable):
    # the printable component contains no data at all and can be ignored,
    # but it will still be passed as a parameter.
    name, pos, velocity, lifetime = ecs.comps_of_eid(eid,
                                                     Comps.NAME,
                                                     Comps.POSITION,
                                                     Comps.VELOCITY,
                                                     Comps.LIFETIME)
    print(f'{name} @ {pos.x, pos.y}, moving towards {velocity.dx, velocity.dy} '
          f'for {lifetime.time_left} seconds')


print('*' * 72)
print('1st run, explicit run_system')
print('*' * 72)
print(f'My walker object is {ten_seconds_walker}')
print(f'It has the following components: {ecs.cids_of_eid(ten_seconds_walker)}')
print(f'All entities: {ecs.eidx}')
print(f'All components: {ecs.cidx}')
print(f'All systems: {ecs.fidx}')

ecs.run_system(1, render_system, Comps.PRINTABLE)
for i in range(15):
    ecs.run_system(1, motion_system, Comps.POSITION, Comps.VELOCITY)
    ecs.run_system(1, lifetime_system, Comps.LIFETIME)
    ecs.run_system(1, render_system, Comps.PRINTABLE)

print(f'All entities: {ecs.eidx}')
print(f'All components: {ecs.cidx}')
print(f'All systems: {ecs.fidx}')

print('*' * 72)
print('2nd run, run_all_systems')
print('*' * 72)
ecs.add_system(motion_system, Comps.POSITION, Comps.VELOCITY)
ecs.add_system(lifetime_system, Comps.LIFETIME)
ecs.add_system(render_system, Comps.PRINTABLE)

ten_seconds_walker = ecs.create_entity(tag='Walker')
ecs.add_component(ten_seconds_walker, Comps.NAME, '10 Seconds Walker')
ecs.add_component(ten_seconds_walker, Comps.POSITION, Position(0, 0))
ecs.add_component(ten_seconds_walker, Comps.VELOCITY, Velocity(0, 5))
ecs.add_component(ten_seconds_walker, Comps.LIFETIME, SimpleNamespace(time_left=10))
ecs.add_component(ten_seconds_walker, Comps.PRINTABLE, True)

print(f'My walker object is {ten_seconds_walker}')
print(f'It has the following components: {ecs.cids_of_eid(ten_seconds_walker)}')
print(f'All entities: {ecs.eidx}')
print(f'All components: {ecs.cidx}')
print(f'All systems: {ecs.fidx}')

for i in range(15):
    ecs.run_all_systems(1)

print(f'All entities: {ecs.eidx}')
print(f'All components: {ecs.cidx}')
print(f'All systems: {ecs.fidx}')
