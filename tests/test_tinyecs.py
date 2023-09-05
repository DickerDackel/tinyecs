import pytest
import re

import tinyecs as ecs

from pgcooldown import Cooldown
from contextlib import nullcontext as does_not_raise
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


@dataclass
class Ping:
    ack: bool = False


def wounding_system(dt, eid, health):
    health.health -= 100
    print(f'\nhealth of {eid} is now {health.health}')
    return health.health


def stats_system(dt, eid, name, health):
    return f'{dt=}, {eid=}, {name.name=}, {health.health=}'


def ping_system(dt, eid, ping):
    ping.ack = True


def move_system(dt, eid, pos, velocity):
    pos.x += velocity.dx * dt
    pos.y += velocity.dy * dt
    return (pos.x, pos.y)


UUID_RE = re.compile('^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')


def setup():
    ecs.reset()
    ecs.add_system(ping_system, 'ping')
    ecs.add_system(stats_system, 'name', 'health')

    return (ecs.create_entity(components={'name': SimpleNamespace(name='Lorem')}),
            ecs.create_entity('player',
                              {'name': SimpleNamespace(name='Ipsum'), 'health': Health()}))


def re_helper(s, re):
    match = re.fullmatch(s)
    return match


def test_entity_creation():
    e1, e2 = setup()
    assert re_helper(str(e1), UUID_RE), "Name doesn't match uuid format"
    assert e2 == 'player', "Name is not 'player'"


def test_add_component():
    e1, e2 = setup()
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

    with pytest.raises(ecs.UnknownEntityError) as e:
        ecs.add_component('xyzzy', 'name', 'Lorem ipsum')
    assert 'not registered' in str(e.value)


def test_remove_component():
    e1, e2 = setup()
    ecs.remove_component(e1, 'health')
    assert 'health' not in ecs.eidx[e1]
    assert 'name' in ecs.eidx[e1]

    e1, e2 = setup()
    ecs.remove_component(e2, 'name', 'health')
    assert 'still alive'
    assert 'name' not in ecs.eidx[e2]
    assert 'health' not in ecs.eidx[e2]

    ecs.remove_component(e1, 'xyzzy')  # must not raise KeyError
    assert 'still alive'


def test_add_system():
    ecs.add_system(stats_system, 'name', 'health')
    ecs.add_system(move_system, 'pos', 'velocity')
    assert ecs.sidx[stats_system] == ('name', 'health')


def test_eids_by_cids():
    e1, e2 = setup()

    # This converting to set and back forces the same order as eids_by_cids
    assert len(ecs.eids_by_cids('name')) == 2
    assert ecs.eids_by_cids('name', 'health')[0][0] == e2

    with pytest.raises(ecs.UnknownComponentError) as e:
        ecs.comp_of_eid('player', 'non-existent-comp')
    assert 'not registered with entity' in str(e.value)


def test_cids_of_eid():
    assert set(ecs.cids_of_eid('player')) == set(['name', 'health'])

    with pytest.raises(ecs.UnknownEntityError) as e:
        ecs.cids_of_eid('missing-entity')
    assert 'not registered' in str(e.value)


def test_comps_of_eid():
    l = len(ecs.cids_of_eid('player'))
    assert type(ecs.comps_of_eid('player', 'health')[0]) == Health
    assert len(ecs.comps_of_eid('player')) == l

    with pytest.raises(ecs.UnknownEntityError) as e:
        ecs.comps_of_eid('missing-entity', 'irrelevant')
    assert 'not registered' in str(e.value)


def test_run_system():
    e1, e2 = setup()
    ecs.run_system(1, wounding_system, 'health')
    assert ecs.eidx[e2]['health'].health == 900
    assert ecs.cidx['health'][e2].health == 900


def test_run_all_systems():
    e1, e2 = setup()
    ecs.add_system(move_system, 'pos', 'velocity')
    ecs.add_system(wounding_system, 'health')
    ecs.add_component(e2, 'pos', SimpleNamespace(x=100, y=200))
    ecs.add_component(e2, 'velocity', SimpleNamespace(dx=5, dy=7))
    res = ecs.run_all_systems(1)

    assert ecs.eidx[e2]['pos'] == SimpleNamespace(x=105, y=207)
    assert res[move_system][e2] == (105, 207)


def test_remove_system():
    ecs.add_system(ping_system, 'ping')
    ecs.add_system_to_domain('test', ping_system)
    ecs.remove_system(ping_system)

    assert ping_system not in ecs.sidx
    assert ping_system not in ecs.didx['test']

    def unregistered_function():
        pass

    ecs.remove_system(unregistered_function)
    assert 'still alive'


def test_remove_entity():
    e1, e2 = setup()
    comps = ecs.comps_of_eid(e1)

    ecs.remove_entity(e1)
    assert e1 not in ecs.eidx
    for c in ecs.cidx:
        assert e1 not in c

    for c in comps:
        assert id(c) not in ecs.oidx

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


def test_eid_of_comp():
    e = ecs.create_entity()
    c = SimpleNamespace(a=1, b=2)
    ecs.add_component(e, 'test', c)
    assert ecs.eid_of_comp(c) == e

    ecs.remove_entity(e)


def test_reset():
    ecs.reset()
    assert len(ecs.eidx) == 0
    assert len(ecs.cidx) == 0
    assert len(ecs.sidx) == 0
    assert len(ecs.didx) == 0
    assert len(ecs.oidx) == 0


def test_kill_from_system():
    def kill_system(dt, eid, kill):
        ecs.remove_entity(eid)

    ecs.reset()
    tiktok = False
    for i in range(10):
        e = ecs.create_entity()
        ecs.add_component(e, 'some-data', True)
        if (tiktok := not tiktok):
            ecs.add_component(e, 'kill', True)

    assert len(ecs.eidx) == 10
    ecs.run_system(1, kill_system, 'kill')
    assert len(ecs.eidx) == 5


def test_add_system_to_domain():
    setup()
    ecs.add_system(ping_system, 'ping')
    ecs.add_system_to_domain('infra', ping_system)

    assert 'infra' in ecs.didx
    assert ping_system in ecs.didx['infra']

    ecs.remove_system(ping_system)
    with pytest.raises(ecs.UnknownSystemError) as e:
        ecs.add_system_to_domain('test', ping_system)
    assert 'not registered' in str(e.value)


def test_remove_system_from_domain():
    ecs.remove_system_from_domain('infra', stats_system)

    assert stats_system not in ecs.didx['infra']
    assert not ecs.remove_system_from_domain('no-domain', stats_system)


def test_run_domain():
    ecs.add_system(ping_system, 'ping')
    ecs.add_system_to_domain('infra', ping_system)

    e = ecs.create_entity()
    ecs.add_component(e, 'ping', Ping(False))

    res = ecs.run_domain(1, 'infra')
    assert ping_system in res
    assert e in res[ping_system]

    res = ecs.run_domain(1, 'non-existent')
    assert res == {}


def test_is_eid():
    e = ecs.create_entity()
    assert ecs.is_eid(e)
    assert not ecs.is_eid('no-eid')


def test_eid_has():
    ecs.reset()
    e1, e2 = setup()
    assert ecs.eid_has(e1, 'non-existent-component') is False
    assert ecs.eid_has(e1, 'non-existent-component', 'name') is False
    assert ecs.eid_has(e2, 'name') is True
    assert ecs.eid_has(e2, 'name', 'health') is True


def test_shutdown():
    ecs.reset()

    shutdown_successful = False

    class ShutdownEntity():
        def shutdown_(self):
            nonlocal shutdown_successful
            shutdown_successful = True

    e = ecs.create_entity()
    ecs.add_component(e, 'shutdown-test', ShutdownEntity())
    ecs.remove_entity(e)
    assert shutdown_successful


def test_cid_of_comp():
    ecs.reset()
    eid = ecs.create_entity()

    cid = ecs.add_component(eid, 'testing', 'Lorem ipsum')
    assert ecs.cid_of_comp(eid, 'Lorem ipsum') == cid

    with pytest.raises(ecs.UnknownEntityError) as e:
        ecs.cid_of_comp(0, 'Lorem ipsum')
    assert 'not registered' in str(e.value)

    with pytest.raises(ecs.UnknownComponentError) as e:
        ecs.cid_of_comp(eid, 'wrong comp')
    assert 'not found in entity' in str(e.value)


def test_healthcheck():
    def _setup():
        ecs.reset()
        eid = ecs.create_entity('my-entity')
        cid = ecs.add_component(eid, 'my-component', True)
        return eid, cid

    eid, cid = _setup()
    print(ecs.eidx)
    print(ecs.cidx)

    del ecs.cidx[cid]
    with pytest.raises(ecs.RegistryError) as e:
        ecs.healthcheck()
    assert 'Component in eidx is missing in cidx' in str(e.value)

    eid, cid = _setup()
    del ecs.cidx[cid][eid]
    with pytest.raises(ecs.RegistryError) as e:
        ecs.healthcheck()
    assert 'Entity in eidx is missing in cidx component' in str(e.value)

    eid, cid = _setup()
    ecs.cidx[cid][eid] = False
    with pytest.raises(ecs.RegistryError) as e:
        ecs.healthcheck()
    assert 'Component object differs between eidx and cidx' in str(e.value)

    eid, cid = _setup()
    del ecs.eidx[eid]
    with pytest.raises(ecs.RegistryError) as e:
        ecs.healthcheck()
    assert 'Entity in cidx is missing in eidx' in str(e.value)

    eid, cid = _setup()
    del ecs.eidx[eid][cid]
    with pytest.raises(ecs.RegistryError) as e:
        ecs.healthcheck()
    assert 'Component in cidx is missing in eidx' in str(e.value)


def test_create_archetype():
    setup()

    assert ('ping',) in ecs.archetype
    assert ('name', 'health') in ecs.archetype


def test_add_to_archetype():
    # Also tests remove_from_archetype
    setup()

    def test_system(dt, eid, test):
        pass

    e = ecs.create_entity()
    ecs.add_component(e, 'test', True)
    ecs.run_system(0, test_system, 'test')
    assert e in ecs.archetype[('test',)]

    ecs.remove_component(e, 'test')
    assert e not in ecs.archetype[('test',)]


def test_comps_of_archetype():
    e1, e2 = setup()

    # [('player', [namespace(name='Ipsum'), Health(health=1000)])]
    run_parms = ecs.comps_of_archetype('name', 'health')
    assert len(run_parms) == 1
    assert run_parms[0][0] == 'player'
    assert len(run_parms[0][1]) == 2


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
    test_eidx_and_cidx_consistent()
    test_eid_of_comp()
    test_reset()
    test_kill_from_system()
    test_add_system_to_domain()
    test_remove_system_from_domain()
    test_run_domain()
    test_is_eid()
    test_eid_has()
    test_shutdown()
    test_healthcheck()
    test_create_archetype()
    test_add_to_archetype()
    test_comps_of_archetype()
