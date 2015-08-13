State Machine Crawler
=====================

A toolkit for following `automata based programming model <http://en.wikipedia.org/wiki/Automata-based_programming>`_
and facilitate the developer with writing `model based tests <http://en.wikipedia.org/wiki/Model-based_testing>`_.

The toolkit is called *State Machine Crawler* instead of plain *State Machine* because it does not just blindly perform
transitions between states but actually finds the shortest path between two states based on the *cost* of all possible
*paths* between them. The ability to find the *shortest path* between multiples states comes from a representation of
the states in the form of a `directed graph <http://en.wikipedia.org/wiki/Directed_graph>`_. Such model allows to employ
pure mathematical algorithms to measure distances between the nodes.

For usage examples please have a look at *tests.py* in the root project directory.

.. toctree::
   :maxdepth: 2

   api