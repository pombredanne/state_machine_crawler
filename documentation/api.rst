API
===

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

State collections
-----------------

.. autoclass:: state_machine_crawler.StateCollection
    :members:


Error class
-----------

.. autoclass:: state_machine_crawler.DeclarationError

.. autoclass:: state_machine_crawler.TransitionError

.. autoclass:: state_machine_crawler.UnreachableStateError

State graph visualization
-------------------------

When state machine gets big it might become difficult to monitor state transitions within it. In such a case a
*WebView* class should be used:

.. autoclass:: state_machine_crawler.WebView

Command line interface
----------------------

In most common case the developer wants to be able to manipulate the `SUT <http://xunitpatterns.com/SUT.html>`_ without
launching python emulator and just use some sort of command line utility.

The package provides an autodiscoverable CLI:

.. autofunction:: state_machine_crawler.entry_point

The CLI as such has the following options:

.. autofunction:: state_machine_crawler.cli
