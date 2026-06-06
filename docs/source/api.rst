tinyecs API
===========

.. contents::
   :class: this-will-duplicate-information-and-it-is-still-useful-here

Primary functions
-----------------

.. autofunction:: tinyecs.create_entity
.. autofunction:: tinyecs.add_component
.. autofunction:: tinyecs.add_components
.. autofunction:: tinyecs.remove_entity
.. autofunction:: tinyecs.remove_component
.. autofunction:: tinyecs.run_system

Requesting components
---------------------

.. autofunction:: tinyecs.comp_of_eid
.. autofunction:: tinyecs.comps_of_eid
.. autofunction:: tinyecs.eid_has

ECS Management
--------------

.. autofunction:: tinyecs.reset

.. _api-bulk-run:

Running systems in bulk
-----------------------

.. autofunction:: tinyecs.run_bulk_system

.. autofunction:: tinyecs.add_system
.. autofunction:: tinyecs.remove_system
.. autofunction:: tinyecs.run_all_systems

.. autofunction:: tinyecs.add_system_to_domain
.. autofunction:: tinyecs.remove_system_from_domain
.. autofunction:: tinyecs.run_domain

Other helpers
-------------

.. autofunction:: tinyecs.cid_of_comp
.. autofunction:: tinyecs.cids_of_eid
.. autofunction:: tinyecs.eid_of_comp
.. autofunction:: tinyecs.eids_by_cids
.. autofunction:: tinyecs.has
.. autofunction:: tinyecs.healthcheck

Archetypes
----------

.. autofunction:: tinyecs.create_archetype
.. autofunction:: tinyecs.add_to_archetype
.. autofunction:: tinyecs.comps_of_archetype
.. autofunction:: tinyecs.remove_archetype
.. autofunction:: tinyecs.remove_from_archetype

Properties
----------
.. autofunction:: tinyecs.set_property
.. autofunction:: tinyecs.set_properties
.. autofunction:: tinyecs.remove_property
.. autofunction:: tinyecs.has_property
.. autofunction:: tinyecs.clear_properties
.. autofunction:: tinyecs.eids_by_property
.. autofunction:: tinyecs.purge_by_property

Exceptions
----------

.. autoexception:: tinyecs.UnknownEntityError
.. autoexception:: tinyecs.UnknownComponentError
.. autoexception:: tinyecs.UnknownSystemError
.. autoexception:: tinyecs.UnknownArchetypeError
.. autoexception:: tinyecs.RegistryError

Type-hinting
------------

For readability in your code, if you use type hinting, tinyecs defines the
following aliases:

.. code-block::

    type EntityID = Hashable
    type ComponentID = Hashable
    type DomainID = Hashable
    type Property = Hashable
    type Component = object
