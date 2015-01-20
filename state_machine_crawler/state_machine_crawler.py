import logging
from inspect import isclass
from abc import ABCMeta, abstractmethod


LOG = logging.getLogger("state_machine_crawler")

ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter("%(message)s"))

LOG.addHandler(ch)


class StateMachineError(Exception):
    """ Base error to be raise by the toolkit """


class TransitionError(StateMachineError):
    """ Raised if the transition could not be performed.

    Failure could happen because:

    - target state is not reachable
    - state verification failed

    NOTE: if transition itself fails (i.e. exception in the *move* method) - the exception is raised as is
    """


class DeclarationError(StateMachineError):
    """ Raised if something is wrong with the state machine declaration in general """


class Transition(object):
    """ Represents a transformation of the system from one state into another

    Transitions have a *_system* attribute that represents the entity with which transitions' states are associated.

    Class definitions of the transitions must have:

    cost (int)
        Relative *price* of the transition. Transitions that take longer time to run are more *expensive*. The *cost*
        has to be experimentally determined.
    target_state (subclass of :class:`State <state_machine_crawler.State>`)
        The state to which the system should be transitioned
    source_state (subclass of :class:`State <state_machine_crawler.State>`)
        The state from which the system should be transitioned

    The only difference between *target_state* and *source_state* is a direction of the relationship.

    Note: there can be only *target_state* or only *source_state* because if a transition from state **A** to state
    **B** is possible it does not at all imply that the opposite transition can be performed the same way.
    """
    __metaclass__ = ABCMeta
    cost = 1
    target_state = source_state = None

    def __init__(self, system):
        self._system = system

    @abstractmethod
    def move(self):
        """
        Performs the actions to move from one state to another.
        """

    @classmethod
    def link(cls, target_state=None, source_state=None):
        """
        Links an existing transition with a specific state.

        This method exists to avoid creating unnecessary subclasses in the situation when multiple states can perform
        similar transitions.
        """
        tstate = target_state
        sstate = source_state

        class NewTransition(cls):
            target_state = tstate
            source_state = sstate
        return NewTransition


class StateMetaClass(ABCMeta):

    def __init__(self, name, bases, attrs):
        super(StateMetaClass, self).__init__(name, bases, attrs)
        self.transition_map = {}
        for name in dir(self):
            attr = getattr(self, name)
            if not (isclass(attr) and issubclass(attr, Transition)):
                continue
            if attr.target_state:
                attr.source_state = self
                if attr.target_state == "self":
                    attr.target_state = self
                    self.transition_map[self] = attr
                else:
                    self.transition_map[attr.target_state] = attr
            elif attr.source_state:
                class RelatedTransition(attr):
                    target_state = self
                RelatedTransition.__name__ = name
                attr.source_state.transition_map[self] = RelatedTransition
            else:
                raise DeclarationError("No target nor source state is defined for %r" % attr)


class State(object):
    """ A base class for any state of the system

    States have a *_system* attribute that represents the entity with which they are associated.
    """
    __metaclass__ = StateMetaClass

    def __init__(self, system):
        self._system = system

    @abstractmethod
    def verify(self):
        """ Checks if the system ended up in a desired state. Should return a boolean. """


def _get_cost(states):
    """ Returns a cumulative cost of the whole chain of transitions """
    cost = 0
    cursor = states[0]
    for state in states[1:]:
        cost += cursor.transition_map[state].cost
        cursor = state
    return cost


def _find_shortest_path(graph, start, end, path=[], get_cost=_get_cost):
    """ Derived from `here <https://www.python.org/doc/essays/graphs/>`_

    Finds the shortest path between two states. Estimations are based on a sum of costs of all transitions.
    """
    path = path + [start]
    if start == end:
        return path
    if start not in graph:
        return None
    shortest = None
    for node in graph[start]:
        if node not in path:
            newpath = _find_shortest_path(graph, node, end, path, get_cost)
            if newpath:
                if not shortest or get_cost(newpath) < get_cost(shortest):
                    shortest = newpath
    return shortest


def _create_transition_map_partial(state, state_map=None):
    """ Returns a graph for state transitioning """
    state_map = state_map or {}
    if state in state_map:
        return state_map
    state_map[state] = set()
    for next_state in state.transition_map.keys():
        state_map[state].add(next_state)
        _create_transition_map_partial(next_state, state_map)
    return state_map


def _create_transition_map(initial_transition):
    initial_state = initial_transition.target_state
    the_map = _create_transition_map_partial(initial_state)
    for source_state, target_states in the_map.iteritems():
        target_states.add(initial_state)
        # TODO: find a way to avoid modifying the class property itself
        source_state.transition_map[initial_state] = initial_transition
    return the_map


class StateMachineCrawler(object):
    """ The crawler is responsible for orchestrating the transitions of system's states

    system
        All transitions shall change the internal state of this object.
    initial_transition (subclass of :class:`InitialTransition <state_machine_crawler.InitialTransition>`)
        The first transition to be executed to move to the initial state

    >>> scm = StateMachineCrawler(system_object, CustomIntialTransition)

    or

    >>> scm = StateMachineCrawler.create(system_object, CustomIntialTransition)
    """

    @classmethod
    def create(cls, system, initial_transition):
        """ Instanciates and returns the crawler with a state that mostly resembles the one the *_system* is in.
        The state does not necessarily have to be the initial one."""
        instance = cls(system, initial_transition)
        longest_distance = 0
        current_state = None
        for state in instance._state_graph:
            if not state(system).verify():
                continue
            shortest_path = _find_shortest_path(instance._state_graph, instance._current_state, state, get_cost=len)
            distance = len(shortest_path)
            if distance > longest_distance:
                longest_distance = distance
                current_state = state
            elif distance < longest_distance:
                pass
            else:
                raise TransitionError("States %r and %r satisfy system's condition" % (current_state, state))
        instance._current_state = current_state
        return instance

    def __init__(self, system, initial_transition):
        if not (isclass(initial_transition) and issubclass(initial_transition, Transition)):
            raise DeclarationError("initial_transition must be a Transition subclass")
        if initial_transition.target_state is None:
            raise DeclarationError("initial transition has no target state")

        self._system = system
        self._current_transition = None
        # placeholders for the classes that caused transition failure
        self._error_states = set()
        self._error_transitions = set()
        self._initial_transition = initial_transition
        self._initial_state = initial_transition.target_state
        self._state_graph = _create_transition_map(initial_transition)

        class EntryPoint(State):

            def verify(self):
                return True

            class initialize(initial_transition):
                pass

        self._state_graph[EntryPoint] = {self._initial_state}
        self._current_state = self._entry_point = EntryPoint

        self._on_state_change = lambda: None
        LOG.info("State machine crawler initialized")

    @property
    def state(self):
        """ Represents a current state of the sytstem """
        return self._current_state

    def _err(self, target_state, msg):
        raise TransitionError("Move from state %r to state %r has failed: %s" % (self._current_state,
                                                                                 target_state, msg))

    def _do_step(self, next_state):
        self._current_transition = transition = self._current_state.transition_map[next_state]
        self._on_state_change()
        try:
            LOG.info("Transition to state %s started", next_state)
            transition(self._system).move()
            LOG.info("Transition to state %s finished", next_state)
            transition_ok = True
        except:
            self._error_transitions.add(transition)
            LOG.exception("Failed to move to: %s", next_state)
            transition_ok = False
        self._on_state_change()
        if not transition_ok:
            self._current_state = self._entry_point
            self._err(next_state, "transition failure")
        try:
            LOG.info("Verification of state %s started", next_state)
            verification_ok = next_state(self._system).verify()
            LOG.info("Verification of state %s finished", next_state)
        except:
            LOG.exception("Failed to verify transition to: %s" % next_state)
            verification_ok = False
        if verification_ok:
            self._current_state = next_state
            LOG.info("State changed to %s", next_state)
            self._on_state_change()
        else:
            self._error_states.add(next_state)
            LOG.error("State verification error for: %s", next_state)
            self._on_state_change()
            self._current_state = self._entry_point
            self._err(next_state, "verification failure")

    def set_on_state_change_handler(self, handler): # pragma: no cover
        self._on_state_change = handler

    def move(self, state):
        """ Performs a transition from the current state to the state passed as an argument

        state (subclass of :class:`State <state_machine_crawler.State>`)
            target state of the system

        >>> scm.move(StateOne)
        >>> scm.state is StateOne
        True
        """
        shortest_path = _find_shortest_path(self._state_graph, self._current_state, state)
        if shortest_path is None:
            raise TransitionError("There is no way to achieve state %r" % state)
        if state is self._current_state:
            next_states = [state]
        else:
            next_states = shortest_path[1:]
        for next_state in next_states:
            self._do_step(next_state)
