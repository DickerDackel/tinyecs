# tinyecs - The teeniesst, tiniest ESC system

After reading part 2 and 3 of these articles:

    https://t-machine.org/index.php/2007/09/03/entity-systems-are-the-future-of-mmog-development-part-1/

I decided to implement an ECS myself, well aware that `esper` is a solid and
long existing implementation, but I wanted to see how to implement it myself.

The base premise is: No OO and entities have *no* data.

So an entity is only a unique identifier.  Components can be anything that can
hold data, e.g. dataclasses

Workflow:

    1. entity = create_entity()
    2. add_component(entity, cid, component}
       ...
    3. add_system(fkt, *cids)
       ...
    4. in game loop run_all_systems(dt)

	alternatively run_system(fkt, *cids)

If a system needs to modify components of other entities, these entities e.g.
the player, need special eids so they can be queried from the registry.

use `comps_of_eid(eid, *comps)` for that.  This way, a bullet component can
substract health from a player entity.

Basic components are in the `tinyecs.components` package.

As of now, please look into the demos folder and read the documentation in the
module.  A longer howto will be added soon.
