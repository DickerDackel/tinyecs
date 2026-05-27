.. tinyecs documentation master file, created by
   sphinx-quickstart on Fri May 15 11:29:54 2026.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

tinyecs documentation
=====================

This is *tinyecs*, the teeniest, tinyest Entity Component System.

.. note::

    *Entity Component System* is generally shortened to *ECS*, which is what
    will be used from here on.

When reading articles about game programming, I stumbled over the concept of
ECS and got curious.  I found `this article
<https://web.archive.org/web/20190913112237/https://t-machine.org/index.php/2007/09/03/entity-systems-are-the-future-of-mmog-development-part-1/>`_
which is sadly no longer available as original, but luckily preserved on the
*waybackmachine*.

After finishing part 3 of that series, I decided to implement an ECS myself.
I did a short research about the available ECS systems for python and pretty
much only found *esper* mentioned.  So I decided to do a clean-room
implementation of my own system without reading more from that article or
looking at existing implementations.

After some back and forth, trying different things, the base premises ended up
as :

* Entities are pure IDs, not objects that contain any data
* No OO
* Framework agnostic

The initial version of what now is tinyecs was about 50 lines of code,
currently it's at 287, which is still pretty small.


.. toctree::
   :maxdepth: 1
   :caption: Contents:

   tutorial
   api
