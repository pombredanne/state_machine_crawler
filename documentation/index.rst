State Machine Crawler
=====================

A toolkit for following `automata based programming model <http://en.wikipedia.org/wiki/Automata-based_programming>`_
and facilitate the developer with writing `model based tests <http://en.wikipedia.org/wiki/Model-based_testing>`_.

The toolkit is called *State Machine Crawler* instead of just *State Machine* because it does not just perform
transitions between states blindly but also finds the shortest path between two states based on the *cost* of all
possible paths between them. The ability to find the path between states comes from a representation of the states
as a `directed graph <http://en.wikipedia.org/wiki/Directed_graph>`_. The model allows to employ pure mathimatical
algoritm to measure distance between the nodes.

Primitives
----------

The primitives of the toolkit are *States* and *Transitions*. The first ones are essentially descriptions of certain
conditions within the system. The latest - are descriptions of how to change the conditions to semantically move
from one state to another.

.. autoclass:: state_machine_crawler.State

.. autoclass:: state_machine_crawler.Transition
    :members:

Built in states and transitions
-------------------------------

.. autoclass:: state_machine_crawler.InitialState

.. autoclass:: state_machine_crawler.InitialTransition
    :members:

.. autoclass:: state_machine_crawler.ErrorState

.. autoclass:: state_machine_crawler.ErrorTransition
    :members:

The crawler
-----------

.. autoclass:: state_machine_crawler.StateMachineCrawler
    :members:

Error class
-----------

.. autoclass:: state_machine_crawler.StateMachineCrawlerError