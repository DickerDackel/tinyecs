Introduction
############

ECS stands for Entity Component System, and it is a programming paradigm that
differs from the well known OO.

During my research I stumbled over `this article`_ and after reading part 2 and
3, I decided to implement an ECS myself, well aware that `esper` is a solid
and long existing implementation, but I wanted to see how to implement it
myself.

.. _this article: https://web.archive.org/web/20250408195932/https://t-machine.org/index.php/2007/09/03/entity-systems-are-the-future-of-mmog-development-part-1/


I'm not trying to sell you an ECS by explaining the problems of multiple
inheritance in game programming.  There are articles out there that do this in
much detail.  If you're here, you're already interested in the concept, so
the tutorial might be a good starting point.  It will create a small demo with
bouncing sprites using pygame-ce.  But tinyecs is platform agnostic, you can
use it with whatever library you like.


Installation
============

tinyecs is available on pip and can be installed by::

    pip install tinyecs

The project is maintained and hosted on `github`_, where you also can find the
wheels for a local install, or install it directly from the cloned repo.

.. _github: https://github.com/dickerdackel/tinyecs

    git clone https://github.com/dickerdackel/tinyecs
    cd tinyecs
    python3 -m venv --prompt tinyecs .venv
    .venv/bin/activate
    # or .venv/Scripts/activate.bat on windows
    pip install .

Documentation
=============

The project home and main documentation is on `Read the Docs`_.

.. _Read the Docs: https://tinyecs.readthedocs.io/

Support / Contributing
======================

Issues can be opened on `github issues`_

.. _github issues: https://github.com/dickerdackel/tinyecs/issues

Please respect, that I don't want any contributions done with the assistance
of AI.  This is a hobby project with focus on the craft of programming.  I
have experimentally used AI to audit parts of the code and documentation, and
while it found a lot of typos and 2 actual issues, without exception, the
provided solutions were often besides the point or plain wrong.

I have no possibility to enforce that request, the simple fact that I ask for
it should be sufficient.

License
=======

This software is provided under the MIT license.

See LICENSE file for details.
