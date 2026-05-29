from collections import defaultdict
from collections.abc import Hashable, Iterable
from typing import Any, Protocol
from uuid import uuid4

__all__ = ['Component', 'ComponentID', 'DomainID', 'EntityID', 'Property',
           'RegistryError', 'UnknownArchetypeError', 'UnknownComponentError',
           'UnknownEntityError', 'UnknownSystemError', 'add_component',
           'add_components', 'add_system', 'add_system_to_domain',
           'add_to_archetype', 'cid_of_comp', 'cids_of_eid',
           'clear_properties', 'comp_of_eid', 'comps_of_archetype',
           'comps_of_eid', 'create_archetype', 'create_entity', 'eid_has',
           'eid_of_comp', 'eids_by_cids', 'eids_by_property', 'has',
           'has_property', 'healthcheck', 'purge_by_property',
           'remove_archetype', 'remove_component', 'remove_entity',
           'remove_from_archetype', 'remove_property', 'remove_system',
           'remove_system_from_domain', 'reset', 'run_all_systems',
           'run_domain', 'run_system', 'set_properties', 'set_property',
           'update_component',]

type EntityID = Hashable
type ComponentID = Hashable
type DomainID = Hashable
type Property = Hashable
type Component = object

type _EntityComponentsBundle = tuple[EntityID, list[Component]]
type _OptionalProperties = Iterable[Property] | None
type _RunSystemResult = dict[EntityID, Any]


# The typehinting system can't work with functions using *args, **kwargs.
# This solution comes from https://docs.python.org/3/library/typing.html#annotating-callable-objects
class SystemFunction(Protocol):
    def __call__(self, dt: float, eid: EntityID, *cids: ComponentID, **kwargs: dict[str, object]) -> Any: ...


eidx = {}  # entity index
cidx = {}  # component id index
sidx = {}  # system index
didx = {}  # domain index
oidx = defaultdict(set)  # object index
plist = defaultdict(set)  # entity property lists
archetype = {}


class UnknownEntityError(Exception):
    """Raised if information from an unknown entity is requested."""
    pass


class UnknownComponentError(Exception):
    """Raised if an unknown component is requested."""
    pass


class UnknownSystemError(Exception):
    """Raised if an unknown system is requested."""
    pass


class UnknownArchetypeError(Exception):
    """Raised if an unknown archetype is requested."""
    pass


class RegistryError(Exception):
    """Raised if an inconsistency is found in the internal ecs registry.

    :param error: The actual error message
    :param eid: The entity ID of the defective registry entry
    :param cid: The component ID of the defective registry entry
    :param component: The component object of the defective registry entry
    :param eid: The properties of the defective registry entry

    Contains an error message and the registry objects that have been
    identified as inconsistent.
    """

    def __init__(self, error, *, eid, cid=None, component=None, other=None, properties=None):
        self.error = error
        self.eid = eid
        self.cid = cid
        self.component = component
        self.other = other
        self.properties = properties


def reset() -> None:
    """Remove everything registered in the ECS.

    Use this to clear everything, e.g. before a new game or when restarting a
    game state.
    """

    eidx.clear()
    cidx.clear()
    sidx.clear()
    didx.clear()
    oidx.clear()
    plist.clear()
    archetype.clear()


def healthcheck() -> bool:
    """Perform a health check on the registry.

    This function checks if the cross references between the entity index and
    the component index are still bi-directional.

    NOTE: This function is performance heavy and not designed to use in a system.
    It's intended for debugging purposes only, e.g. after setting a breakpoint.

    Returns
    -------
    bool
        True if successful, RegistryError exception otherwise.

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
    for eid in plist:
        if eid not in eidx:
            raise RegistryError('Unknown entity in property list', eid=eid, properties=plist[eid])
        ...  # FIXME

    return True


def create_entity(tag: EntityID = None,
                  components: dict[ComponentID, Component] | None = None,
                  properties: _OptionalProperties = None) -> EntityID:
    """Create a new entity

    Parameters
    ----------
    tag:
        an optional ID for the entity, e.g. "player"
        if no tag is passed, a uuid is generated

    components:
        A dict with component IDs as keys and components as values (see add_component)

    properties:
        An iterable of properties

    Returns
    -------
    Hashable
        The entity ID.  Same as given if one is passed, otherwise a uuid4
    """

    eid = tag if tag else str(uuid4())
    eidx[eid] = {}

    # Add optionally passed components
    if components:
        add_components(eid, components)

    if properties:
        set_properties(eid, properties)

    return eid


def remove_entity(eid: EntityID) -> None:
    """Remove an entity from the system.

    Removes all bindings to components and the entity_id itself from the
    registry.

    non-existent entity_ids will be silently ignored

    Parameters
    ----------
    eid: hashable
        The entity ID

    Returns
    -------
    None
    """

    # Ignore unknown eids, since we're removing anyways
    try:
        cids = eidx[eid].keys()
    except KeyError:
        pass
    else:
        remove_component(eid, *cids)

    try:
        del plist[eid]
    except KeyError:
        pass

    remove_from_archetype(eid)

    try:
        del eidx[eid]
    except KeyError:
        pass


def add_component(eid: EntityID, cid: ComponentID, comp: Component) -> ComponentID:
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

    # Make sure, when replacing a component, the the old one is removed from
    # oidx for this entity.
    try:
        old_comp = id(eidx[eid][cid])
        oidx[old_comp].discard(eid)
        if not oidx[old_comp]:
            del oidx[old_comp]
    except KeyError:
        pass

    cidx[cid][eid] = comp
    eidx[eid][cid] = comp
    oidx[id(comp)].add(eid)

    add_to_archetype(eid)

    return cid


update_component = add_component


def add_components(eid: EntityID, components: dict[ComponentID, Component]) -> list[ComponentID]:
    """A convenience wrapper around add_component

    Parameters
    ----------
    components:
        A dict with component IDs as keys and components as values (see add_component)

    Returns
    -------
    None
    """

    return [add_component(eid, cid, comp) for cid, comp in components.items()]


def remove_component(eid: EntityID, *cids: ComponentID) -> None:
    """Remove one or more components from an entity.

    Parameters
    ----------
    eid:
        The entity to remove the component from

    cids:
        The component ids to remove

    If the component has a shutdown_ attribute, it is assumed to be a list of
    zero parameter functions to be called in order.

    Note: If the entity no longer exists, the error is silently ignored.

    Returns
    -------
    None
    """

    for cid in cids:
        remove_from_archetype(eid, cid)

        # Ignore unknown cids or eids since we're removing anyways
        # Also, no need to try each on their own
        try:
            obj = cidx[cid][eid]
            obj_id = id(obj)
            del cidx[cid][eid]
            del eidx[eid][cid]
            oidx[obj_id].discard(eid)
            if not oidx[obj_id]:
                del oidx[id(obj)]
        except KeyError:
            pass
        else:
            if hasattr(obj, 'shutdown_'):
                obj.shutdown_()


def add_system(fkt: SystemFunction, *cids: ComponentID) -> None:
    r"""Add a system for the specifiied cids.

    Parameters
    ----------

    fkt:
        The system function

        The prototype for the function is

            fkt(delta_time, eid, \*comps)

        where delta_time is e.g. the miliseconds from a pygame tick.  eid is the id
        of the entity that matches, and \*comps are all requested components for
        this specific entity.

        This function is called for every entity that matches all specified
        component ids.

    \*cids:
        The component ids that are required for this system

    Returns
    -------
    None

    Note
    ----
    Registering a system automatically creates an `archetype` from the given `cids`
    """

    create_archetype(*cids)
    sidx[fkt] = cids


def remove_system(fkt: SystemFunction) -> None:
    """Remove the given function from the registry.

    Parameters
    ----------
    fkt:
        The system function

    Remove the match for this function from the registry

    Returns
    -------
    None

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


def add_system_to_domain(domain: DomainID, system: SystemFunction) -> None:
    """Create or extend a domain with the given system.

    Domains are collections of systems that can run with a single function
    call run_domain.

    Note that the system must first be registered with add_system

        add_system_to_domain('render-phase', draw_system)

    Parameters
    ----------
    system: Callable
        The system function

    Returns
    -------
    None
    """

    if domain not in didx:
        didx[domain] = set()
    if system not in sidx:
        raise UnknownSystemError(f'system {system} is not registered')
    didx[domain].add(system)


def remove_system_from_domain(domain: DomainID, system: SystemFunction) -> None:
    """Remove a registered system from the given domain.

    Parameters
    ----------
    system: Callable
        The system function

    Returns
    -------
    None

    Note
    ----
    If the system is not in the domain, the error is silently ignored.
    """

    if domain not in didx:
        return
    try:
        didx[domain].remove(system)
    except KeyError:
        pass


def has(eid: EntityID, has_properties: _OptionalProperties = None) -> bool:
    """Check if the given eid is valid.

    There is no reason to not use `eid in tinyecs.eidx`.  This is just for
    people who prefer a functional interface.

    Parameters
    ----------
    eid
        The entity to verify

    has_properties
        Optional set of required properties

    Returns
    -------
    bool
        True if the eid is valid
    """

    if has_properties is None:
        return eid in eidx

    property_filter = set(has_properties)
    return eid in eidx and property_filter <= plist[eid]


def eid_has(eid: EntityID, *cids: ComponentID) -> bool:
    """check if entity eid has all listed cids.

    Parameters
    ----------
    *cids:
        All component ids that need to match

    Returns
    -------
    bool
        True if all given cids are available for the specified eid
    """

    e = eidx[eid]
    for cid in cids:
        if cid not in e:
            return False

    return True


def eids_by_cids(*cids: ComponentID, has_properties: _OptionalProperties = None) -> list[tuple[EntityID, list[Component]]]:
    """get eids that match all specified cids

    Parameters
    ----------

    *cids:
        All component ids that need to match

    has_properties: set|tuple|list
        Optional set/tuple/list of required properties

    Returns
    -------
    list
        A list of tuples of entity IDs and components
    """

    res = []
    at = tuple(cids)
    if at in archetype:
        return comps_of_archetype(*cids, has_properties=has_properties)

    if has_properties:
        property_filter = set(has_properties)

    for e, have_comps in eidx.items():
        if has_properties and not property_filter <= plist[e]:
            continue

        comps = []
        for c in cids:
            if c in have_comps:
                comps.append(have_comps[c])
            else:
                break
        else:
            res.append((e, comps))
    return res


def cids_of_eid(eid: EntityID) -> list[ComponentID]:
    """Return the list of component IDs of the specified entity

    Parameters
    ----------
    eid: hashable
        The entity ID

    Returns
    -------
    list
        List of component IDs of this entity

    Raises
    ------
    UnknownEntityError
        If the entity is not registered (anymore).
    """

    if eid not in eidx:
        raise UnknownEntityError(f'Entity {eid} is not registered')

    return list(eidx[eid].keys())


def comps_of_eid(eid: EntityID, *cids: ComponentID) -> list[Component]:
    """Get components from the eid for the specified cids.

    While cids_of_eid gets component IDs, this function now gets the actual
    components containing the data.

    if cids is empty or None, returns all components of eid.

    Parameters
    ----------
    eid:
        the entity id from which to get the components

    cids:
        the list of components to fetch

    Returns
    -------
    list
        The (filtered) components of eid

    Raises
    ------
    UnknownEntityError
        If the entity is not registered (anymore).

    UnknownComponentError
        If the passed component couldn't be found.
    """

    if eid not in eidx:
        raise UnknownEntityError(f'Entity {eid} is not registered')

    if not cids:
        return list(eidx[eid].values())

    try:
        return [eidx[eid][cid] for cid in cids]
    except KeyError as e:
        raise UnknownComponentError(f'Component {e} not registered with entity {eid}') from e


def comp_of_eid(eid: EntityID, cid: ComponentID) -> Component:
    """Get a single component from an entity.

    Parameters
    ----------
    eid:
        the entity id from which to get the component

    cid:
        the component id to filter for

    Returns
    -------
    component: object
        The requested component of the given entity ID
    """

    return comps_of_eid(eid, cid)[0]


def eid_of_comp(comp: Component) -> set(EntityID):
    """Find the entity id for object comp.

    Parameters
    ----------
    comp:
        the component to find the entity of

    Returns
    -------
    entity_id
        The entity_id the given component belongs to
    """

    return oidx[id(comp)]


def cid_of_comp(eid: EntityID, comp: Component) -> ComponentID:
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


def run_system(dt: float,
               fkt: SystemFunction,
               *cids: ComponentID,
               has_properties: _OptionalProperties = None,
               **kwargs: dict[str, Any]) -> _RunSystemResult:
    """Run the system for the matching cids.

    Parameters
    ----------
    dt:
        delta time since the last frame (miliseconds)

    fkt:
        the actual system function

    *cids:
        the components to run on

    has_properties:
        set of required properties

    The fkt gets the list of all entities that contain the listed
    components.  The list can further be narrowed down my filtering for given
    properties.  Then it runs the function for every entity and the requested
    components, passing dt as heartbeat.

    This function is a direct call.  Alternatively, you can use add_system
    combined with run_all_systems or run_domain below.

    Returns
    -------
    dict
        A dictionary with entity IDs as key and the function result as value
    """

    at = tuple(cids)
    if at not in archetype:
        create_archetype(*cids)

    adict = archetype[at]
    # need to get call_list upfront, since kill_system could modify the dict
    # Also: not running in the if clause is vastly faster than checking an
    # empty set.
    if has_properties:
        property_filter = set(has_properties)
        call_list = [(eid, *parms) for eid, parms in adict.items()
                     if property_filter <= plist[eid]]
    else:
        call_list = [(eid, *parms) for eid, parms in adict.items()]
    return {eid: fkt(dt, eid, *parms, **kwargs) for eid, *parms in call_list}


def run_all_systems(dt: float) -> dict[SystemFunction, _RunSystemResult]:
    """Run all registered systems

    This calls above run_system for all registered systems with their
    appropriate components.

    Parameters
    ----------

    dt:
        delta time

    Returns
    -------
    dict
        A dict of function as key, and the result of run_system as value
    """

    return {fkt: run_system(dt, fkt, *comps)
            for fkt, comps in sidx.items()}


def run_domain(dt: float, domain: DomainID) -> dict[SystemFunction, _RunSystemResult]:
    """Run all systems within domain.

    This is the same as run_all_systems, but limited to a specific domain.

    Parameters
    ----------
    dt:
        delta time

    Returns
    -------
    dict
        A dict of function as key, and the result of run_system as value
    """

    if domain not in didx:
        return {}

    return {fkt: run_system(dt, fkt, *sidx[fkt])
            for fkt in didx[domain]}


def create_archetype(*cids: ComponentID) -> None:
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


def remove_archetype(cids: Iterable[ComponentID]) -> None:
    """Remove an archetype from the system. (See `add_archetype`).

    Parameters
    ----------
    cids
        The list of component IDs that construct the archetype.

    Returns
    -------
    None
    """

    at = tuple(cids)
    del archetype[at]


def add_to_archetype(eid: EntityID) -> None:
    """Make sure, eid is registered with all appropriate archetypes.

    Parameters
    ----------
    eids
        The entity ID to add to the archetype

    There should be no need to call this function manually.  It's called
    internally, when a new component is added to an entity which makes this
    entity belong into an archetype it wasn't a member of before.
    """

    have_comps = set(cids_of_eid(eid))
    for at in archetype:
        s = set(at)
        if s <= have_comps:
            archetype[at][eid] = comps_of_eid(eid, *at)


def remove_from_archetype(eid: EntityID, cid: ComponentID | None = None) -> None:
    """Make sure, eid is only registered with appropriate archetypes.

    Parameters
    ----------
    eids
        The entity ID to remove from the archetype

    cid
        An optional component ID.

    There should be no need to call this function manually.  It's called
    internally, when a component is removed from an entity, so that the entity
    no longer belongs to that archetype.
    """

    for at, adict in archetype.items():
        if eid in adict and (cid is None or cid in at):
            del adict[eid]


def comps_of_archetype(*cids: ComponentID, has_properties: _OptionalProperties = None) -> list[_EntityComponentsBundle]:
    """Return the given archetype.

    Primarily used by `run_system`.

    Returns a list of tuples consisting of eid and components.

    Parameters
    ----------
    cids
        The cids that define the archetype.

    has_properties
        Optional set of required properties

    Returns
    -------
    List[tuple[Hashable, list[object]]]

        A list of tuples of (eid, components)

    Raises
    ------
    UnknownArchetypeError
        If the given archetype doesn't exist.
    """

    at = tuple(cids)
    if at not in archetype:
        raise UnknownArchetypeError

    if has_properties:
        property_filter = set(has_properties)
        return [(e, comps)
                for e, comps in archetype[at].items()
                if property_filter <= plist[e]]
    else:
        return [(e, comps) for e, comps in archetype[at].items()]


def set_property(eid: EntityID, property: Property) -> None:
    """Add a property to the given entity.

    Parameters
    ----------
    eid: hashable
        The entity id to add the component to

    property: hashable
        A flag or tag that can be filtered, e.g. 'is_drawable'

    Returns
    -------
    None

    Raises
    ------
    UnknownEntityError
        If the entity is not registered (anymore).
    """

    if eid not in eidx:
        raise UnknownEntityError(f'Entity {eid} is not registered')

    plist[eid].add(property)


def set_properties(eid: EntityID, properties: Iterable[Property]) -> None:
    """Add a list of properties to the given entity.

    Parameters
    ----------
    eid
        The entity ID to add the properties to.

    property:
        The list of properties to add.

    This is just a convenience wrapper around `set_property`.
    """
    for prop in properties:
        set_property(eid, prop)


def has_property(eid: EntityID, prop: Property) -> bool:
    """Checks if the given entity has that property.

    Parameters
    ----------
    eid: hashable
        The entity id to add the component to

    property: hashable
        The property to check for

    Returns
    -------
    bool

    Raises
    ------
    UnknownEntityError
        If the entity is not registered (anymore).
    """

    if eid not in eidx:
        raise UnknownEntityError(f'Entity {eid} is not registered')

    return prop in plist[eid]


def remove_property(eid: EntityID, prop: Property) -> None:
    """Removes a property from the given entity.

    Parameters
    ----------
    eid: hashable
        The entity id to add the component to

    property: hashable
        The property to remove

    Returns
    -------
    None

    Raises
    ------
    UnknownEntityError
        If the entity is not registered (anymore).
    """

    if eid not in eidx:
        raise UnknownEntityError(f'Entity {eid} is not registered')

    plist[eid].remove(prop)


def clear_properties(eid: EntityID) -> None:
    """Removes all properties from the given entity.

    Parameters
    ----------
    eid: hashable
        The entity id to add the component to

    Returns
    -------
    None

    Raises
    ------
    UnknownEntityError
        If the entity is not registered (anymore).
    """

    if eid not in eidx:
        raise UnknownEntityError(f'Entity {eid} is not registered')

    plist[eid] = set()


def eids_by_property(*properties: Property) -> list[EntityID]:
    """Get a list of entities that match all given properties.

    Parameters
    ----------
    *properties:
        All properties that need to match

    Returns
    -------
    list[EntityID]
        Entities matching the given properties

    """

    property_filter = set(properties)

    return [eid for eid, props in plist.items() if property_filter <= props]


def purge_by_property(*properties: Property) -> None:
    """Purge entities that match all given properties.

    This is useful to clean up all entities belonging to a sub state without
    impacting the remaining registry.

    Parameters
    ----------

    *properties:
        All properties that need to match
    """

    for eid in eids_by_property(*properties):
        remove_entity(eid)
