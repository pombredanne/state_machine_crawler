from inspect import isclass
from abc import ABCMeta, abstractmethod


class StateMachineCrawlerError(Exception):
    """ Error to be raised when:

    - there are issues with initialization of the state state machine
    - it is impossible to perform state transition because the state is unreachable
    """


class Transition(object):
    """ Represents a transformation of the system from one state into another

    Transitions have *_system* attribute that represents the entity with which all the states are associated.

    Class definition of the transition must have:

    cost (int)
        Relative *price* of the transition. Transitions that take longer time to run are more *expensive*. The *cost*
        has to be experimentally determined.
    target_state (subclass of :class:`State <state_machine_crawler.State>`)
        The state to which the system should be transitioned
    source_state (subclass of :class:`State <state_machine_crawler.State>`)
        The state from which the system should be transitioned

    The only difference between *target_state* and *source_state* is a direction of the relationship.

    Note: there can be only *target_state* or only *source_state* because if a transition from state **A** to state
    **B** is possible it does not imply that the opposite transition is possible.
    """
    __metaclass__ = ABCMeta
    cost = 1
    target_state = source_state = None

    def __init__(self, system):
        self._system = system

    @abstractmethod
    def move(self):
        """
        Performs the actions to move from state one to state two.
        """

    @classmethod
    def link(cls, target_state=None, source_state=None):
        """
        Links an existing transition with a specific state.

        This method exists to avoid creating unnecessary subclasses in the situation when multiple states can perform
        the similar transitions.
        """
        tstate = target_state
        sstate = source_state

        class NewTransition(cls):
            target_state = tstate
            source_state = sstate
        return NewTransition


class StateMetaClass(type):

    def __init__(self, name, bases, attrs):
        super(StateMetaClass, self).__init__(name, bases, attrs)
        self.transition_map = {}
        for name in dir(self):
            attr = getattr(self, name)
            if not (isclass(attr) and issubclass(attr, Transition)):
                continue
            if attr.target_state:
                if attr.target_state == "self":
                    attr.target_state = self
                    self.transition_map[self] = attr
                else:
                    self.transition_map[attr.target_state] = attr
            elif attr.source_state:
                class RelatedTransition(attr):
                    target_state = self
                    source_state = None
                attr.source_state.transition_map[self] = RelatedTransition
            else:
                raise StateMachineCrawlerError("No target nor source state is defined for %r" % attr)


class State(object):
    """ A base class for any state of the system """
    __metaclass__ = StateMetaClass


class InitialState(State):
    """ Represents the initial state of the system. The initial state is reachable from ANY other state. """


class InitialTransition(Transition):
    """ A special transformation that configures the system to a blank state.

    It must be possible to perform the transition at any point. I.e. all the states should be transitionable to
    the initial state. It might me the most expensive transition in the system.

    The transition is bound with :class:`InitialState <state_machine_crawler.InitialState>`. This should not be changed.
    """
    target_state = InitialState

    @abstractmethod
    def move(self):
        """ Any code responsible for configuring the system should be placed here """


class ErrorState(State):
    """ Represents a state of the system with abnormal conditions """


class ErrorTransition(Transition):
    """ Base class for managing a transition of the system into the ErrorState.

    Exception is available as *_error* instance attribute.

    The transition is bound with :class:`ErrorState <state_machine_crawler.ErrorState>`. This should not be changed.
    """
    target_state = ErrorState

    def __init__(self, system, error):
        super(ErrorTransition, self).__init__(system)
        self._error = error

    @abstractmethod
    def move(self):
        """ All error logging and/or error handling should be implemented here """


def _get_cost(states):
    """ Returns a cumulative cost of the whole chain of transitions """
    cost = 0
    cursor = states[0]
    for state in states[1:]:
        cost += cursor.transition_map[state].cost
        cursor = state
    return cost


def _find_shortest_path(graph, start, end, path=[]):
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
            newpath = _find_shortest_path(graph, node, end, path)
            if newpath:
                if not shortest or _get_cost(newpath) < _get_cost(shortest):
                    shortest = newpath
    return shortest


def _create_transition_map(state, state_map=None):
    """ Returns a graph for state transitioning """
    state_map = state_map or {}
    if state in state_map:
        return state_map
    state_map[state] = set()
    for next_state in state.transition_map.keys():
        state_map[state].add(next_state)
        _create_transition_map(next_state, state_map)
    return state_map


class StateMachineCrawler(object):
    """ The crawler is responsible for orchestrating the transitions of system's states

    system
        All transition shall change its state.
    initial_transition (subclass of :class:`InitialTransition <state_machine_crawler.InitialTransition>`)
        The first transition to be executed
    error_transition (subclass of :class:`ErrorTransition <state_machine_crawler.ErrorTransition>`)
        The transition to be executed when exceptional situation takes place

    >>> scm = StateMachineCrawler(system_object, CustomIntialTransition, CustomErrorTransition)
    """

    def __init__(self, system, initial_transition, error_transition):
        self._system = system
        self._current_state = None
        if not (isclass(initial_transition) and issubclass(initial_transition, InitialTransition)):
            raise StateMachineCrawlerError("initial_transition must be InitialTransition subclass")
        if not (isclass(error_transition) and issubclass(error_transition, ErrorTransition)):
            raise StateMachineCrawlerError("error_transition must be ErrorTransition subclass")
        self._initial_transition = initial_transition
        self._initial_state = initial_transition.target_state
        self._error_transition = error_transition
        self._state_graph = self._init_state_graph()

    def _init_state_graph(self):
        initial_state = self._initial_transition.target_state
        if initial_state is None:
            raise StateMachineCrawlerError("Initial transition has no target state")
        state_graph = _create_transition_map(initial_state)
        for source_state, target_states in state_graph.iteritems():
            target_states.add(initial_state)
            if source_state == initial_state:
                continue
            source_state.transition_map[initial_state] = self._initial_transition
        return state_graph

    @property
    def state(self):
        """ Represents a current state of the sytstem """
        return self._current_state

    def move(self, state):
        """ Performs a transition from the current state to the state passed as the argument

        state (subclass of :class:`State <state_machine_crawler.State>`)
            target state of the system

        >>> scm.move(StateOne)
        >>> scm.state is StateOne
        True
        """
        if state is self._initial_state or self._current_state is None:
            self._initial_transition(self._system).move()
            self._current_state = self._initial_state
            if state is self._initial_state:
                return
        shortest_path = _find_shortest_path(self._state_graph, self._current_state, state)
        if shortest_path is None:
            raise StateMachineCrawlerError("There is no way to achieve state %r" % state)
        if state is self._current_state:
            next_states = [state]
        else:
            next_states = shortest_path[1:]
        for next_state in next_states:
            transition = self._current_state.transition_map[next_state]
            try:
                transition(self._system).move()
                self._current_state = next_state
            except Exception, error:
                self._error_transition(self._system, error).move()
                self.move(self._initial_state)
                break
