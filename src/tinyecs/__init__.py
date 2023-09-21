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
archetype = {}


class UnknownEntityError(KeyError):
    pass


class UnknownComponentError(KeyError):
    pass


class UnknownSystemError(KeyError):
    pass


class UnknownArchetypeError(KeyError):
    pass


class RegistryError(RuntimeError):
    def __init__(self, error, eid, cid, component, other=None):
        self.error = error
        self.eid = eid
        self.cid = cid
        self.component = component
        self.other = other


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
    archetype.clear()


def healthcheck():
    """Perform a health check on the registry.

    This function checks if the cross references between the entity index and
    the component index are still bi-directional.

    Returns
    -------
    bool
        True if successful, exception otherwise.

    Raises
    ------
    RegistryError(error, eid, cid, component, other=None)
        error       verbose error message
        eid         id of entity
        cid         id of component
        component   component object
        other       component in other index or None

    """
    for eid in eidx:
        for cid in eidx[eid]:
            if cid not in cidx:
                raise RegistryError('Component in eidx is missing in cidx', eid=eid, cid=cid, component=eidx[eid][cid])
            if eid not in cidx[cid]:
                raise RegistryError('Entity in eidx is missing in cidx component', eid=eid, cid=cid, component=eidx[eid][cid])
            if eidx[eid][cid] is not cidx[cid][eid]:
                raise RegistryError('Component object differs between eidx and cidx', eid=eid, cid=cid, component=eidx[eid][cid], other=cidx[cid][eid])
    for cid in cidx:
        for eid in cidx[cid]:
            if eid not in eidx:
                raise RegistryError('Entity in cidx is missing in eidx', eid=eid, cid=cid, component=cidx[cid][eid])
            if cid not in eidx[eid]:
                raise RegistryError('Component in cidx is missing in eidx', eid=eid, cid=cid, component=cidx[cid][eid])

    return True


def create_entity(tag=None, components=None):
    """Create a new entity

        create_entity(tag=None, **kwargs) --> entity_id

    Arguments:
        tag         an optional ID for the entity, e.g. "player"
                    if no tag is passed, a uuid is generated

        **kwargs	A list of component-IDs and components

    """
    eid = tag if tag else str(uuid4())
    eidx[eid] = {}

    # Add optionally passed components
    if components:
        add_components(eid, components)

    return eid


def remove_entity(eid):
    """Remove an entity from the system

        remove_entity(entity_id, postponed=False) -> None

    Removes all bindings to components and the entity_id itself from the
    registry.

    non-existent entity_ids will be silently ignored

    """
    # Ignore unknown eids, since we're removing anyways
    try:
        cids = eidx[eid].keys()
    except KeyError:
        return

    remove_from_archetype(eid)

    remove_component(eid, *cids)
    del eidx[eid]


def add_component(eid, cid, comp):
    """Add a component to the registry.

    Parameters
    ----------
    eid: hashable
        The entity id to add the component to

    cid: hashable
        An identifier for the component This will be used to assign systems to
        entities

    comp: *
        The actual data object A comp can be anything that holds data, just a
        string, e.g. a name, a SimpleNamespace, a dataclass, ...

        Note: Technically, there is no reason a comp object couldn't have
        methods, but by concept, functionality is reserved for the System
        working on the components, not the component itself.

    Returns
    -------
    cid: hashable
        The `cid` that was put in as an argument.

    Raises
    ------
    UnknownEntityError
        If the `eid` doesn't exist in the registry.

    """
    if eid not in eidx:
        raise UnknownEntityError(f'Entity {eid} is not registered')

    if cid not in cidx:
        cidx[cid] = {}

    cidx[cid][eid] = comp
    eidx[eid][cid] = comp
    oidx[id(comp)] = eid

    add_to_archetype(eid)

    return cid


update_component = add_component


def add_components(eid, components):
    for cid, comp in components.items():
        add_component(eid, cid, comp)


def remove_component(eid, *cids):
    """remove components from an entity

        remove_component(eid, cid) -> None

    Arguments:

        eid		The entity to remove the component from
        cids    The component ids to remove

    If the component has a shutdown_ attribute, it is assumed to be a list of
    zero parameter functions to be called in order.
    """
    for cid in cids:
        remove_from_archetype(eid, cid)

        # Ignore unknown cids or eids since we're removing anyways
        # Also, no need to try each on their own
        try:
            obj = cidx[cid][eid]
            del cidx[cid][eid]
            del eidx[eid][cid]
            del oidx[id(obj)]
        except KeyError:
            pass
        else:
            if hasattr(obj, 'shutdown_'):
                obj.shutdown_()


def add_system(fkt, *cids):
    """Add a system for the specifiied cids

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

    Note
    ----
    Registering a system automatically creates an `archetype` from the given `cids`
    """
    create_archetype(*cids)
    sidx[fkt] = cids


def remove_system(fkt):
    """remove the function from the registry

        remove_system(fkt) -> None

    Arguments:

        fkt		the system function it does

    Remove the match for this function from the registry

    Note
    ----
    In contrast to `add_system`, an existing `archetype` is not automatically
    removed.
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


def has(eid):
    """Check if eid is valid.

    There is no reason to not use `eid in tinyecs.eidx`.  This is just for
    people who prefer a functional interface.

    Parameters
    ----------
    eid
        The entity to verify

    Returns
    -------
    bool
        True if the eid is valid

    """
    return eid in eidx


is_eid = has
is_eid.__doc__ = """For backward compatibility.  Use `tinyecs.has(eid)` instead."""


def eid_has(eid, *cids):
    """check if entity eid has all listed cids.

        eid_has(*cids) -> bool

    Arguments:

        *cids		All component ids that need to match

    """
    e = eidx[eid]
    for cid in cids:
        if cid not in e:
            return False
    return True


def eids_by_cids(*cids):
    """get eids that match all specified cids

        eids_by_cid(*cids) -> [(eid, comps), ...]

    Arguments:

        *cids		All component ids that need to match

    """
    res = []
    at = tuple(cids)
    if at in archetype:
        return comps_of_archetype(*cids)

    for e, have_comps in eidx.items():
        comps = []
        for c in cids:
            if c in have_comps:
                comps.append(have_comps[c])
            else:
                break
        else:
            res.append((e, comps))
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


def cid_of_comp(eid, comp):
    """Get the cid of a component.

    A system only receives an actual component, but cannot know under which
    name this was targetted.  This function searches the cid of the given
    component.

    Note: This is a relatively expensive operation, but since it will mostly
    be used to clean up old connections between entities, it should be a
    one-shot and worth the price.

    Parameters
    ----------
    eid: hashable
        The entity ID

    comp: object
        The component to identify

    Returns
    -------
    hashable
        The cid that the given component was added under.

    Raises
    ------
    UnknownEntityError
        If the entity is not registered (anymore).

    UnknownComponentError
        If the passed component couldn't be found.

    """
    if not has(eid):
        raise UnknownEntityError(f'Entity {eid} is not registered')

    cids = cids_of_eid(eid)
    for cid in cids:
        if eidx[eid][cid] is comp:
            return cid

    raise UnknownComponentError(f'Component {comp} not found in entity {eid}')


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
    at = tuple(cids)
    if at not in archetype:
        create_archetype(*cids)

    adict = archetype[at]
    # need to get call_list upfront, since kill_system could modify the dict
    call_list = [(eid, *parms) for eid, parms in adict.items()]
    return {eid: fkt(dt, eid, *parms, **kwargs) for eid, *parms in call_list}


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


def create_archetype(*cids):
    """Create an archetype from the provided cids.

    An archetype is a fixed combination of components.  Each time a component
    is added or removed from an entity, that entity and its components are
    added/removed from the archetype.

    This removes the need to search through all entities for the matching cids
    in favour of returning the finished list directly.

    Since every system is usually run every frame, there are a *lot* of
    searches, which is very expensive.

    The cost to insert/remove an entity into/from the archetype is a rather
    small operation that is only done when the entity is changed.

    Note
    ----
    Archetypes are created automatically as soon as a system runs for the
    first time.  Manually creating an archetype is only useful if a function
    wishes to work on a set of entities outside the `run_system` framework.

    Parameters
    ----------
    cids
        The list of cids that define the archetype.

        Note: Order is important, since the system relies on it.

    Returns
    -------
    None

    """
    at = tuple(cids)
    if at in archetype:
        return

    archetype[at] = dict(eids_by_cids(*cids))


def remove_archetype(cids):
    """Remove an archetype from the system. (See `add_archetype`)"""
    at = tuple(cids)
    del archetype[at]


def add_to_archetype(eid):
    """Make sure, eid is registered with all appropriate archetypes."""
    have_comps = set(cids_of_eid(eid))
    for at in archetype:
        s = set(at)
        if s <= have_comps:
            archetype[at][eid] = comps_of_eid(eid, *at)


def remove_from_archetype(eid, cid=None):
    """Make sure, eid is only registered with appropriate archetypes."""
    for at, adict in archetype.items():
        if eid in adict and (cid is None or cid in at):
            del adict[eid]


def comps_of_archetype(*cids):
    """Return the given archetype.

    Primarily used by `run_system`.
    
    Returns a list of tuples consisting of eid and components.

    Parameters
    ----------
    cids
        The cids that define the archetype.

    Returns
    -------
    List[tuple[Hashable, list[object]]

        A list of tuples of (eid, components)

    Raises
    ------
    UnknownArchetypeError
        If the given archetype doesn't exist.

    """

    at = tuple(cids)
    if at not in archetype:
        raise UnknownArchetypeError

    return [(e, comps) for e, comps in archetype[at].items()]
