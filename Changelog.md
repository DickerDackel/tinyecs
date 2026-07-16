# v0.4.0 - BREAKING CHANGE

- Bugfix: Typo in typehinting removed
- Bugfix: The bulk runner was called even when no system entities matched.
- Enhancement: EntityComponentBundle type is now public
- API change: Got rid of mandatory ``dt``

This release gets rid of the design flaw of mandatory deltatime.

Having made deltatime a requirement for all systems and the runner calls was a
mistake from the beginning, since a lot of systems just don't need it.

To adapt to the new call signature you have to

- Remove the first parameter for `dt` of all system functions and the various
  ecs.run_* functions.
- systems that actually do make use of deltatime, can receive it as a kwarg inkstead:

    # From
    def momentum_system(dt, eid, position, momentum):...

    # To
    def momentum_system(eid, position, momentum, *, dt):...

    # From
    ecs.run_system(dt, 'position', 'momentum')

    # To
    ecs.run_system('position', 'momentum', dt=deltatime)

The drawback is, that if you use `run_all_systems` and `run_domain`, all
systems that don't need deltatime need an additional `**kwargs` at the end of
their argument list, since those run-functions pass given kwargs to all
registered systems.

# v0.3.6
- New API: run_bulk_system
- Cosmetics: replace germanism `fkt` with `fn`

# v0.3.5
- pyproject.toml still pointed to README.md, thus no introduction on pypi

# v0.3.4
- Bugfix: Empty archetype was created with full component list instead of empty.
- Bugfix: Don't nuke the entity when calling create_entity on an existing eid.
- Docs: Changed docstrings to reST
- Docs: Far more complete

# v0.3.3

- Sphinx docs
- Lots of docstring cleanups and enhancements
- experimental stubs removed, type hints are now embedded
- BREAKING CHANGE - oidx must be a set, since an object can be registered with multiple entities
- various minor cleanups and enhancements

# v0.3.2

- Better defaults
- Removed leftover code from older versions
- Fixes outdated imports
- Fix has_properties parameter

# v0.3.1

- New function `purge_by_property`
- linter fixes, slight optimizations

# v0.3.0

- Properties!

# v0.2.10

- Fixed docs

# v0.2.9
- Follow API change in pgcooldown
- Simplified archetype creation
- global was bullshit there
- Formatting fixes (hopefully)

# v0.2.8
- Tutorial!

# v0.2.7
- Archetypes!
- More test objects, better readable output
- FPS in titlebar and release boxes on mouseclick
- Just standardized the FPS display in the titlebar

# v0.2.6
- Removed double function is_eid
- Fix for pygame.transform.rotozoom changing the surface type
- New function cid_of_comp
- Merge branch 'main' of https://github.com/dickerdackel/tinyecs
- The interface to deadzone_system was b0rken

# v0.2.5
- The interface to deadzone_system was b0rken
- typos and clarifications
- Merge branch 'main' of https://github.com/dickerdackel/tinyecs

# v0.2.4

- Friction system added
- Use locking in RSAI, round RSA to allow caching
- Renamed components to compsys, backward compat preserved
- Added default wildcard exports
- Removed fragment of no longer existing code
- Added registry healthcheck
- tinyecs.has added

# v0.2.3

- Back to alphabetic ordering, since these are all unrelated
- `wsad_system` added
- New class `RSAImage`
- Updated `ESprite`, added `EVsprite`
