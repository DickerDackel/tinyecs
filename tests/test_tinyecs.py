import pytest
import re

import tinyecs as ecs

from dataclasses import dataclass
from types import SimpleNamespace


@dataclass
class Velocity:
    dx: float = 0.0
    dy: float = 0.0


@dataclass
class Health:
    health: int = 1000


@dataclass
class SomeFlag:
    flag: bool = False


def wounding_system(dt, eid, health_comp):
    health_comp.health -= 100
    return health_comp.health


def stats_system(dt, eid, name_comp, health_comp):
    return f'dt={dt}, entity={eid}, name={name_comp.name}, health={health_comp.health}'


def move_system(dt, eid, pos, velocity):
    pos.x += velocity.dx * dt
    pos.y += velocity.dy * dt
    return (pos.x, pos.y)


UUID_RE = re.compile('^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')

e1 = ecs.create_entity(name=SimpleNamespace(name='Lorem'),
                       health=Health())
e2 = ecs.create_entity('player', name=SimpleNamespace(name='Ipsum'),
                       health=Health())


def re_helper(s, re):
    match = re.fullmatch(s)
    return match


def test_entity_creation():
    assert re_helper(str(e1), UUID_RE), "Name doesn't match uuid format"
    assert e2 == 'player', "Name is not 'player'"


def test_add_component():
    ecs.add_component(e1, 'pos', SimpleNamespace(x=100, y=200))
    ecs.add_component(e1, 'someflag', SomeFlag())
    ecs.add_component(e2, 'pos', SimpleNamespace(x=100, y=200))
    ecs.add_component(e2, 'velocity', Velocity(dx=5, dy=7))
    ecs.add_component(e2, 'someflag', SomeFlag())

    assert ecs.eidx[e1]['name'].name == 'Lorem'
    assert ecs.eidx[e2]['name'].name == 'Ipsum'
    assert ecs.cidx['name'][e1].name == 'Lorem'
    assert ecs.cidx['name'][e2].name == 'Ipsum'
    assert ecs.eidx[e2]['velocity'].dx == 5
    assert ecs.eidx[e2]['health'].health == 1000

    with pytest.raises(KeyError) as e:
        ecs.add_component('xyzzy', 'name', 'Lorem ipsum')
    assert 'xyzzy not registered' in str(e.value)


def test_remove_component():
    ecs.remove_component(e1, 'pos')
    ecs.remove_component(e1, 'health')
    assert 'pos' not in ecs.eidx[e1]
    assert 'health' not in ecs.eidx[e1]
    assert 'name' in ecs.eidx[e1]

    ecs.remove_component(e1, 'xyzzy')
    assert 'still alive'


def test_add_system():
    ecs.add_system(stats_system, 'name', 'health')
    ecs.add_system(move_system, 'pos', 'velocity')
    assert ecs.fidx[stats_system] == ('name', 'health')


def test_eids_by_cids():
    # This converting to set and back forces the same order as eids_by_cids
    assert ecs.eids_by_cids('name') == list(set([e1, e2]))
    assert ecs.eids_by_cids('name', 'health') == [e2]
    assert ecs.eids_by_cids('velocity') == [e2]


def test_cids_of_eid():
    assert sorted(ecs.cids_of_eid('player')) == sorted(['name', 'health', 'pos', 'velocity', 'someflag'])


def test_comps_of_eid():
    l = len(ecs.cids_of_eid('player'))
    assert type(ecs.comps_of_eid('player', 'health')[0]) == Health
    assert len(ecs.comps_of_eid('player')) == l


def test_run_system():
    ecs.run_system(1, wounding_system, 'health')
    assert ecs.eidx[e2]['health'].health == 900
    assert ecs.cidx['health'][e2].health == 900


def test_run_all_systems():
    res = ecs.run_all_systems(1)
    assert ecs.eidx[e2]['pos'] == SimpleNamespace(x=105, y=207)
    assert res[stats_system][e2] == 'dt=1, entity=player, name=Ipsum, health=900'
    assert res[move_system][e2] == (105, 207)


def test_remove_system():
    assert stats_system in ecs.fidx

    ecs.remove_system(stats_system)
    assert stats_system not in ecs.fidx

    res = ecs.run_all_systems(1)
    assert stats_system not in res

    def unregistered_function():
        pass

    ecs.remove_system(unregistered_function)
    assert 'still alive'


def test_remove_entity():
    ecs.remove_entity(e1)
    assert e1 not in ecs.eidx
    for c in ecs.cidx:
        assert e1 not in c

    ecs.remove_entity('xyzzy')
    assert 'still alive'


def test_eidx_and_cidx_consistent():
    for eid in ecs.eidx:
        for cid in ecs.eidx[eid]:
            assert cid in ecs.cidx
            assert ecs.eidx[eid][cid] == ecs.cidx[cid][eid]

    for cid in ecs.cidx:
        for eid in ecs.cidx[cid]:
            assert eid in ecs.eidx
            assert ecs.eidx[eid][cid] == ecs.cidx[cid][eid]


if __name__ == '__main__':
    test_entity_creation()
    test_add_component()
    test_remove_component()
    test_add_system()
    test_eids_by_cids()
    test_cids_of_eid()
    test_comps_of_eid()
    test_run_system()
    test_run_all_systems()
    test_remove_system()
    test_remove_entity()
