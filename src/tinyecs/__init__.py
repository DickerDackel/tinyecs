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

    :returns: True if successful, RegistryError exception otherwise.
    :raises RegistryError: If inconsistencies are found in the registry.

    This function checks if the cross references between the entity index and
    the component index are still bi-directional.

    .. note:: This function is performance heavy and not designed to use in a
        system. It's intended for debugging purposes only, e.g. after setting a
        breakpoint.
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
    """Create a new entity.

    :param tag: an optional ID for the entity, e.g. "player" if no tag is passed, a uuid is generated
    :param components: A dict with component IDs as keys and components as values (see add_component)
    :param properties: An iterable of properties
    :return: The entity ID.  Same as given if one is passed, otherwise a uuid4
    """

    eid = tag if tag else str(uuid4())
    if eid not in eidx:
        eidx[eid] = {}

    # Add optionally passed components
    if components:
        add_components(eid, components)

    if properties:
        set_properties(eid, properties)

    return eid


def remove_entity(eid: EntityID) -> None:
    """Remove an entity from the system.

    :param eid: The entity ID
    :returns: None

    Removes all bindings to components and the entity_id itself from the
    registry.

    .. note:: Non-existent entity_ids will be silently ignored.
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

    :param eid: The entity id to add the component to
    :param cid: An identifier for the component This will be used to assign systems to entities
    :param comp: The actual data object A comp can be anything that holds data, just a string, e.g. a name, a SimpleNamespace, a dataclass, ...
    :return: The `cid` that was put in as an argument.
    :raises UnknownEntityError: If the `eid` doesn't exist in the registry.

    .. note:: Technically, there is no reason a comp object couldn't
        have methods, but by concept, functionality is reserved for the System
        working on the components, not the component itself.
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
    """A convenience wrapper around add_component.

    :param components: A dict with component IDs as keys and components as values (see add_component)
    :return: None
    """

    return [add_component(eid, cid, comp) for cid, comp in components.items()]


def remove_component(eid: EntityID, *cids: ComponentID) -> None:
    r"""Remove one or more components from an entity.

    :param eid: The entity to remove the component from
    :param cids: The component ids to remove
    :return: None

    If the component has a shutdown\_ attribute, it is assumed to be a list of
    zero parameter functions to be called in order.

    .. note:: If the entity no longer exists, the error is silently ignored.

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


def add_system(fn: SystemFunction, *cids: ComponentID) -> None:
    r"""Add a system for the specifiied cids.

    :param fn: The system function
    :param cids: The component ids that are required for this system
    :return: None

    The prototype for the function is::

        fn(delta_time, eid, *comps)

    where delta_time is e.g. the miliseconds from a pygame tick.  eid is the id
    of the entity that matches, and \*comps are all requested components for
    this specific entity.

    This function is called for every entity that matches all specified
    component ids.

    .. note:: Registering a system automatically creates an `archetype` from the given `cids`
    """

    create_archetype(*cids)
    sidx[fn] = cids


def remove_system(fn: SystemFunction) -> None:
    """Remove the given function from the registry.

    :param fn: The system function
    :return: None

    Remove the match for this function from the registry

    .. note:: In contrast to `add_system`, an existing `archetype` is not automatically removed.
    """

    for domain in didx:
        remove_system_from_domain(domain, fn)

    # Ignore unregistered systems, since we're removing anyways
    try:
        del sidx[fn]
    except KeyError:
        pass


def add_system_to_domain(domain: DomainID, system: SystemFunction) -> None:
    """Create or extend a domain with the given system.

    :param system: The system function
    :return: None

    Domains are collections of systems that can run with a single function
    call run_domain.

    .. important:: The system must first be registered with add_system.
    """

    if domain not in didx:
        didx[domain] = set()
    if system not in sidx:
        raise UnknownSystemError(f'system {system} is not registered')
    didx[domain].add(system)


def remove_system_from_domain(domain: DomainID, system: SystemFunction) -> None:
    """Remove a registered system from the given domain.

    :param system: The system function
    :return: None

    .. note:: If the system is not in the domain, the error is silently ignored.
    """

    if domain not in didx:
        return
    try:
        didx[domain].remove(system)
    except KeyError:
        pass


def has(eid: EntityID, has_properties: _OptionalProperties = None) -> bool:
    """Check if the given eid is valid.

    :param eid: The entity to verify
    :param has_properties: Optional set of required properties
    :return: True if the eid is valid

    .. note:: There is no reason to not use `eid in tinyecs.eidx`.  This is
        just for people who prefer a functional interface.
    """

    if has_properties is None:
        return eid in eidx

    property_filter = set(has_properties)
    return eid in eidx and property_filter <= plist[eid]


def eid_has(eid: EntityID, *cids: ComponentID) -> bool:
    """Check if entity eid has all listed cids.

    :param cids: All component ids that need to match
    :return: True if all given cids are available for the specified eid
    """

    e = eidx[eid]
    for cid in cids:
        if cid not in e:
            return False

    return True


def eids_by_cids(*cids: ComponentID, has_properties: _OptionalProperties = None) -> list[tuple[EntityID, list[Component]]]:
    """Get eids that match all specified cids.

    :param cids: All component ids that need to match
    :param as_properties: Optional set/tuple/list of required properties
    :return: A list of tuples of entity IDs and components
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
    """Return the list of component IDs of the specified entity.

    :param eid: The entity ID
    :return: List of component IDs of this entity
    :raises UnknownEntityError: If the entity is not registered (anymore).
    """

    if eid not in eidx:
        raise UnknownEntityError(f'Entity {eid} is not registered')

    return list(eidx[eid].keys())


def comps_of_eid(eid: EntityID, *cids: ComponentID) -> list[Component]:
    """Get components from the eid for the specified cids.

    :param eid: the entity id from which to get the components
    :param cids: the list of components to fetch
    :return: The (filtered) components of eid
    :raises UnknownEntityError: If the entity is not registered (anymore).
    :raises UnknownComponentError: If the passed component couldn't be found.

    While cids_of_eid gets component IDs, this function now gets the actual
    components containing the data.

    .. note:: If cids is empty or None, returns all components of eid.
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

    :param eid: The entity id from which to get the component
    :param cid: The component id to filter for
    :return: The requested component of the given entity ID
    """

    return comps_of_eid(eid, cid)[0]


def eid_of_comp(comp: Component) -> set(EntityID):
    """Find the entity id for object comp.

    :param comp: The component to find the entity of
    :return: The entity_id the given component belongs to
    """

    return oidx[id(comp)]


def cid_of_comp(eid: EntityID, comp: Component) -> ComponentID:
    """Get the cid of a component.

    :param eid: The entity ID
    :param comp: The component to identify
    :return: The cid that the given component was added under.
    :raises UnknownEntityError: If the entity is not registered (anymore).
    :raises UnknownComponentError: If the passed component couldn't be found.

    A system only receives an actual component, but cannot know under which
    name this was targetted.  This function searches the cid of the given
    component.

    .. note:: This is a relatively expensive operation, but since it will
        mostly be used to clean up old connections between entities, it should
        be a one-shot and worth the price.
    """

    if not has(eid):
        raise UnknownEntityError(f'Entity {eid} is not registered')

    cids = cids_of_eid(eid)
    for cid in cids:
        if eidx[eid][cid] is comp:
            return cid

    raise UnknownComponentError(f'Component {comp} not found in entity {eid}')


def _create_call_list(cids: tuple[ComponentID],
                      has_properties: _OptionalProperties) -> list[tuple[EntityID, Component]]:
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
    return call_list


def run_system(dt: float,
               fn: SystemFunction,
               *cids: ComponentID,
               has_properties: _OptionalProperties = None,
               **kwargs: dict[str, Any]) -> _RunSystemResult:
    """Run the system for the matching cids.

    :param dt: delta time since the last frame (miliseconds)
    :param fn: the actual system function
    :param cids: the components to run on
    :param has_properties: set of required properties
    :return: A dictionary with entity IDs as key and the function result as value

    For every entity that has all the listed components, ``fn`` is run.  The
    function prototype of ``fn`` is::

        def callback(dt: float, eid: EntityID, *comps: Component) -> Any

    The list can further be narrowed down my filtering for given properties.

    This function is a direct call.  Alternatively, you can use add_system
    combined with run_all_systems or run_domain below.
    """

    call_list = _create_call_list(cids, has_properties)
    return {eid: fn(dt, eid, *parms, **kwargs) for eid, *parms in call_list}


def run_bulk_system(dt: float,
                    fn: SystemFunction,
                    *cids: ComponentID,
                    has_properties: _OptionalProperties = None,
                    **kwargs: dict[str, Any]) -> Any:
    """Run the bulk system for all entities with matching cids.

    :param dt: delta time since the last frame (miliseconds)
    :param fn: the actual system function
    :param cids: the components to run on
    :param has_properties: set of required properties
    :return: A dictionary with entity IDs as key and the function result as value

    The fn is called with a list of entity ID and components tuples of all
    entities that contain the listed components.  The list can further be
    narrowed down my filtering for given properties.

    ``fn`` is called given a list of ``(EntityID, (components,...))``. In
    contrast to ``run_system``, the user is responsible to loop over the list.

    The prototype of ``fn`` is::

        def callback(dt: call_list: list[tuple[EntityID, list[Component]]]) -> Any
    """

    call_list = _create_call_list(cids, has_properties)
    return fn(dt, call_list, **kwargs)


def run_all_systems(dt: float) -> dict[SystemFunction, _RunSystemResult]:
    """Run all registered systems.

    :param dt: Delta time
    :return: A dict of function as key, and the result of run_system as value

    This calls above run_system for all registered systems with their
    appropriate components.
    """

    return {fn: run_system(dt, fn, *comps)
            for fn, comps in sidx.items()}


def run_domain(dt: float, domain: DomainID) -> dict[SystemFunction, _RunSystemResult]:
    """Run all systems within domain.

    :param dt: Delta time
    :return: A dict of function as key, and the result of run_system as value

    This is the same as run_all_systems, but limited to a specific domain.
    """

    if domain not in didx:
        return {}

    return {fn: run_system(dt, fn, *sidx[fn])
            for fn in didx[domain]}


def create_archetype(*cids: ComponentID) -> None:
    """Create an archetype from the provided cids.

    :param cids: The list of cids that define the archetype.
    :return: None

    An archetype is a fixed combination of components.  Each time a component
    is added or removed from an entity, that entity and its components are
    added/removed from the archetype.

    This removes the need to search through all entities for the matching cids
    in favour of returning the finished list directly.

    Since every system is usually run every frame, there are a *lot* of
    searches, which is very expensive.

    The cost to insert/remove an entity into/from the archetype is a rather
    small operation that is only done when the entity is changed.

    .. note:: Archetypes are created automatically as soon as a system runs
        for the first time.  Manually creating an archetype is only useful if
        a function wishes to work on a set of entities outside the
        `run_system` framework.

    .. important: The order of the given cids is important, since the system relies on it.
    """

    at = tuple(cids)
    if at in archetype:
        return

    archetype[at] = dict(eids_by_cids(*cids)) if at else {eid: [] for eid in eidx}


def remove_archetype(cids: Iterable[ComponentID]) -> None:
    """Remove an archetype from the system. (See `add_archetype`).

    :param cids: The list of component IDs that construct the archetype.
    :return: None
    """

    at = tuple(cids)
    del archetype[at]


def add_to_archetype(eid: EntityID) -> None:
    """Make sure, eid is registered with all appropriate archetypes.

    :param eids: The entity ID to add to the archetype

    There should be no need to call this function manually.  It's called
    internally, when a new component is added to an entity which makes this
    entity belong into an archetype it wasn't a member of before.
    """

    have_comps = set(cids_of_eid(eid))
    for at in archetype:
        if not at:
            archetype[at][eid] = []
        else:
            s = set(at)
            if s <= have_comps:
                archetype[at][eid] = comps_of_eid(eid, *at)


def remove_from_archetype(eid: EntityID, cid: ComponentID | None = None) -> None:
    """Make sure, eid is only registered with appropriate archetypes.

    :param eids: The entity ID to remove from the archetype
    :param cid: An optional component ID.

    There should be no need to call this function manually.  It's called
    internally, when a component is removed from an entity, so that the entity
    no longer belongs to that archetype.
    """

    for at, adict in archetype.items():
        if eid in adict and (cid is None or cid in at):
            del adict[eid]


def comps_of_archetype(*cids: ComponentID, has_properties: _OptionalProperties = None) -> list[_EntityComponentsBundle]:
    """Return the given archetype.

    :param cids: The cids that define the archetype.
    :param has_properties: Optional set of required properties
    :return: A list of tuples of (eid, components)
    :raises UnknownArchetypeError: If the given archetype doesn't exist.

    Primarily used internally by `run_system`.

    Returns a list of tuples consisting of eid and components.
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

    :param eid: The entity id to add the component to
    :param property: A flag or tag that can be filtered, e.g. 'is_drawable'
    :return: None
    :raises UnknownEntityError: If the entity is not registered (anymore).
    """

    if eid not in eidx:
        raise UnknownEntityError(f'Entity {eid} is not registered')

    plist[eid].add(property)


def set_properties(eid: EntityID, properties: Iterable[Property]) -> None:
    """Add a list of properties to the given entity.

    :param eid: The entity ID to add the properties to.
    :param property: The list of properties to add.

    This is just a convenience wrapper around `set_property`.
    """
    for prop in properties:
        set_property(eid, prop)


def has_property(eid: EntityID, prop: Property) -> bool:
    """Checks if the given entity has that property.

    :param eid: The entity id to add the component to
    :param property: The property to check for
    :return: True if the property is set for the given entity
    :raises UnknownEntityError: If the entity is not registered (anymore).
    """

    if eid not in eidx:
        raise UnknownEntityError(f'Entity {eid} is not registered')

    return prop in plist[eid]


def remove_property(eid: EntityID, prop: Property) -> None:
    """Removes a property from the given entity.

    :param eid: The entity id to add the component to
    :param property: The property to remove
    :return: None
    :raises UnknownEntityError: If the entity is not registered (anymore).
    """

    if eid not in eidx:
        raise UnknownEntityError(f'Entity {eid} is not registered')

    plist[eid].remove(prop)


def clear_properties(eid: EntityID) -> None:
    """Removes all properties from the given entity.

    :param eid: The entity id to add the component to
    :return: None
    :raises UnknownEntityError: If the entity is not registered (anymore).
    """

    if eid not in eidx:
        raise UnknownEntityError(f'Entity {eid} is not registered')

    plist[eid] = set()


def eids_by_property(*properties: Property) -> list[EntityID]:
    """Get a list of entities that match all given properties.

    :param properties: All properties that need to match
    :return: Entities matching the given properties

    """

    property_filter = set(properties)

    return [eid for eid, props in plist.items() if property_filter <= props]


def purge_by_property(*properties: Property) -> None:
    """Purge entities that match all given properties.

    :param properties: All properties that need to match

    This is useful to clean up all entities belonging to a sub state without
    impacting the remaining registry.
    """

    for eid in eids_by_property(*properties):
        remove_entity(eid)
