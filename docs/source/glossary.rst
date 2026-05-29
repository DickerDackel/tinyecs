Glossary
========

.. glossary::

   Archetype
      Archetypes provide quick access to combinations of components.

   Component
      Data that belongs to an :term:`Entity`.

   ComponentID
      As with :term:`EntityID`, component IDs allow filtering entities by
      which components they contain.

   Domain
      A collection of :term:`Systems <System>` bundled under a common name.

   ECS
   Entity Component System
      The programming paradigm this package is all about.  *ECS* replaces
      object oriented programming and inheritance with an engine that runs
      systems on combinations of components.

      Read the link given in :doc:`Introduction <introduction>` for a full description.

   Entity
      The representation of an object in *ECS*.  With *tinyecs*, this is just
      an identifier

   EntityID
      The identifier of an entity that's used to access data in the *ECS*.

   Property
      A property is just a label that belongs to an entity.  It can be used by
      functions like :py:func:`tinyecs.run_system` to add additional filtering
      besides the combination of components.

   pygame-ce
      A few years ago, the frequent contributors to the "original" *pygame*
      decided to fork the project after the person who manages the github
      site and the domain frequently got unresponsive for months and progress
      was stalling.

      This resulted in the `pygame-ce`_ project which is actively maintained,
      has seen a plethora of optimizations since the fork, and is with very
      few exceptions a drop-in replacement for *pygame*.  As of this
      writing, *pygame* hasn't been updated in 1.5 years and doesn't
      provide wheels for the latest python version, and platforms other
      than windows.

   System
      The functions that replace methods in object oriented programming.
      Systems get called with a set of components they work on.

.. _pygame-ce: https://github.com/pygame-community/pygame-ce
