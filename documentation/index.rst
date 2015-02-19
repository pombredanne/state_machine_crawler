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

Primitives
----------

The primitives of the toolkit are *States* and *Transitions*. The first ones are essentially descriptions of certain
conditions within the system. The latest - are descriptions of how to change the conditions to perform a semantic move
from one state to another.

.. autoclass:: state_machine_crawler.State
    :members:

.. autofunction:: state_machine_crawler.transition

The crawler
-----------

.. autoclass:: state_machine_crawler.StateMachineCrawler
    :members:

Error class
-----------

.. autoclass:: state_machine_crawler.DeclarationError

.. autoclass:: state_machine_crawler.TransitionError

State graph visualization
-------------------------

When state machine gets big it might become difficult to monitor state transitions within it. In such a case a
*WebView* class should be used:

.. autoclass:: state_machine_crawler.WebView

Command line interface
----------------------

In most common case the developer wants to be able to manipulate the
`SUT <http://en.wikipedia.org/wiki/System_under_test>`_ without launching python emulator and just use some sort of
command line utility. The package provides the following function:

.. autofunction:: state_machine_crawler.cli