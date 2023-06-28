"""tinyecs - The teeniesst, tiniest ESC system

This is implemented after quick reading part 2 and 3 of

https://t-machine.org/index.php/2007/09/03/entity-systems-are-the-future-of-mmog-development-part-1/

The base premise is: No OO and entities have *no* data.

So an entity is only a unique identifier.  Components can be anything that can
hold data.

Workflow:

    1. entity = create_entity()
       ...
    2. add_component(entity, cid, component}
       ...
    3. add_system(fkt, *cids)
       ...
    4. in game loop run_all_systems(dt)

    alternatively

    3. run_system(fkt, *cids)
       ...

If a system needs to modify components of other entities, these entities e.g.
the player, need special eids so they can be queried from the registry.

use comps_of_eid(eid, *comps) for that.  This way, a bullet component can
substract health from a player entity.
"""

from uuid import uuid4

eidx = {}  # entity index
cidx = {}  # component id index
sidx = {}  # system index
didx = {}  # domain index
oidx = {}  # object index

kill_list = []  # postponed kills 


class UnknownEntityError(KeyError):
    pass


class UnknownComponentError(KeyError):
    pass


class UnknownSystemError(KeyError):
    pass


def reset():
    """Remove everything registered in the ECS.

        ecs.reset() -> None

    Use this to clear everything, e.g. before a new game
    """
    eidx.clear()
    cidx.clear()
    sidx.clear()
    didx.clear()
    oidx.clear()


def create_entity(tag=None, components=None):
    """Create a new entity

        create_entity(tag=None, **kwargs) --> entity_id

    Arguments:
        tag         an optional ID for the entity, e.g. "player"
                    if no tag is passed, a uuid is generated

        **kwargs	A list of component-IDs and components

    """
    global eidx, cidx

    eid = tag if tag else str(uuid4())
    eidx[eid] = {}

    # Add optionally passed components
    if components:
        add_components(eid, components)

    return eid


def remove_entity(eid, postponed=False):
    """Remove an entity from the system

        remove_entity(entity_id, postponed=False) -> None

    Removes all bindings to components and the entity_id itself from the
    registry.

    non-existent entity_ids will be silently ignored

    If postponed is True: The entity will *not* be killed but added to a
    kill_list.  Call purge_kill_list() to really remove the entities from the
    system.

    This is useful for entities that want to remove themselves from the ecs in
    a system.  It avoids the system running over a dict that is modified during
    the loop.
    """
    if postponed:
        kill_list.append(eid)
    else:
        _remove_entity(eid)


def _reap_kill_list():
    """Purge entities that are only marked to kill.  See remove_entity with
    'postponed=True'
    """
    for e in kill_list:
        _remove_entity(e)

    kill_list.clear()


def _remove_entity(eid):
    # Ignore unknown eids, since we're removing anyways
    try:
        cids = eidx[eid].keys()
    except KeyError:
        return

    for cid in cids:
        try:
            obj = cidx[cid][eid]
            del cidx[cid][eid]
            del oidx[id(obj)]
        except KeyError:
            # ignore missing components, just try the others
            pass

    del eidx[eid]


def add_component(eid, cid, comp):
    """add a component to the registry

        add_component(eid, cid, comp) -> None

    Arguments:

        eid         The entity id to add the component to
        cid         An identifier for the component
                    This will be used to assign systems to entities
        comp        The actual data object
                    A comp can be anything that holds data, just a string, e.g.
                    a name, a SimpleNamespace, a dataclass, ...

        Note, that technically, there is no reason a comp object couldn't have
        methods, but by concept, functionality is reserved for the System
        working on the components, not the component itself.
    Long description
    """
    global eidx, cidx, oidx

    if eid not in eidx:
        raise UnknownEntityError(f'Entity {eid} is not registered')

    if cid not in cidx:
        cidx[cid] = {}

    cidx[cid][eid] = comp
    eidx[eid][cid] = comp
    oidx[id(comp)] = eid


update_component = add_component


def add_components(eid, components):
    for cid, comp in components.items():
        add_component(eid, cid, comp)


def remove_component(eid, cid):
    """remove a component from an entity

        remove_component(eid, cid) -> None

    Arguments:

        eid		The entity to remove the component from
        cid     The component id to remove

    """
    global eidx, cidx

    # Ignore unknown cids or eids since we're removing anyways
    # Also, no need to try each on their own
    try:
        obj = cidx[cid][eid]
        del cidx[cid][eid]
        del eidx[eid][cid]
        del oidx[id(obj)]
    except KeyError:
        pass


def add_system(fkt, *comps):
    """Add a system for the specifiied comps

        add_system(fkt, *cids) -> None

    Arguments:

        fkt		The system function

        *cids   The component ids that are required for this system

    The prototype for the function is

        fkt(delta_time, eid, *comps)

    where delta_time is e.g. the miliseconds from a pygame tick.  eid is the id
    of the entity that matches, and *comps are all requested components for
    this specific entity.

    This function is called for every entity that matches all specified
    component ids.
    """
    sidx[fkt] = comps


def remove_system(fkt):
    """remove the function from the registry

        remove_system(fkt) -> None

    Arguments:

        fkt		the system function it does

    Remove the match for this function from the registry
    """
    for domain in didx:
        remove_system_from_domain(domain, fkt)

    # Ignore unregistered systems, since we're removing anyways
    try:
        del sidx[fkt]
    except KeyError:
        pass


def add_system_to_domain(domain, system):
    if domain not in didx:
        didx[domain] = set()
    if system not in sidx:
        raise UnknownSystemError(f'system {system} is not registered')
    didx[domain].add(system)


def remove_system_from_domain(domain, system):
    if domain not in didx:
        return
    try:
        didx[domain].remove(system)
    except KeyError:
        pass


def eids_by_cids(*cids):
    """get eids that match all specified cids

        eids_by_cid(*cids) -> [eids]

    Arguments:

        *cids		All component ids that need to match

    """
    res = []
    for e in eidx:
        complete = True
        for c in cids:
            if c not in eidx[e]:
                complete = False
                break
        if complete:
            res.append(e)

    return res


def cids_of_eid(eid):
    """return a list of component ids of the specified entity

        cids_of_eid(eid) -> [cids]

    Arguments:

        arg		what it does
        ...
    Long description
    """
    if eid not in eidx:
        raise UnknownEntityError(f'Entity {eid} is not registered')

    return list(eidx[eid].keys())


def comps_of_eid(eid, *cids):
    """get components from the eid for the specified cids

        comps_of_eid(eid, *cids) -> [components]

    Arguments:

        eid		the entity id from which to get the components
        cids    the list of components to fetch

    While cids_of_eid gets component IDs, this function now gets the actual
    components containing the data.
    """
    if eid not in eidx:
        raise UnknownEntityError(f'Entity {eid} is not registered')

    if not cids:
        return eidx[eid].values()

    try:
        return [eidx[eid][cid] for cid in cids]
    except KeyError as e:
        raise UnknownComponentError(f'Component {e} not registered with entity {eid}') from e


def comp_of_eid(eid, cid):
    """get a single component from an entity

        comp_of_eid(eid, cid) -> component

    Arguments:

        eid     the entity id from which to get the component
        cid     the component id to filter for

    Returns:

        component

    long description...
    """
    return comps_of_eid(eid, cid)[0]


def eid_of_comp(comp):
    """find the entity id for object comp

        eid_of_comp(cid) -> entity

    Arguments:

        comp     the component to find the entity of

    Returns:

        entity
    """
    return oidx[id(comp)]


def run_system(dt, fkt, *cids, **kwargs):
    """run the system for the matching cids

        run_system(dt, fkt, *cids) -> {eid: fkt(dt, eid, *comps), ...}

    Arguments:

        dt		delta time since the last frame (miliseconds)
        fkt     the actual system function
        *cids   the components to run on

    This function gets the list of all entities that contain the listed
    components.  Then it runs the function for every entity and the requested
    components, passing dt as heartbeat.

    This function is a direct call.  Alternatively, you can use add_system
    combined with run_all_systems below.
    """
    res = {}
    for e, have_comps in eidx.items():
        comps = []
        complete = True
        for c in cids:
            if c in have_comps:
                comps.append(have_comps[c])
            else:
                complete = False
                break
        if complete:
            res[e] = fkt(dt, e, *comps, **kwargs)

    if kill_list:
        _reap_kill_list()

    return res


def run_all_systems(dt):
    """Run all registered systems

        run_all_systems(dt) -> {system: run_system-result, ...}

    Arguments:

        dt		delta time

    This calls above run_system for all registered systems with their
    appropriate components.
    """
    return {fkt: run_system(dt, fkt, *comps)
            for fkt, comps in sidx.items()}


def run_domain(dt, domain):
    """Run all systems within domain

        run_domain(dt) -> {system: run_system-result, ...}

    Arguments:

        dt      delta time

    This is the same as run_all_systems, but limited to a specific domain.
    """
    if domain not in didx:
        return {}

    return {fkt: run_system(dt, fkt, *sidx[fkt])
            for fkt in didx[domain]}
