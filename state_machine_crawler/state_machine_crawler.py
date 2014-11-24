from inspect import isclass
from abc import ABCMeta, abstractmethod


class StateMachineCrawlerError(Exception):
    pass


class Transition(object):
    """ Represents a transformation of the system from one state into another """
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
        Links an existing transition with a specific state
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
                self.transition_map[attr.target_state] = attr
            elif attr.source_state:
                class RelatedTransition(attr):
                    target_state = self
                    source_state = None

                attr.source_state.transition_map[self] = RelatedTransition
            else:
                raise StateMachineCrawlerError("No target nor source state is defined for %r" % attr)


class State(object):
    __metaclass__ = StateMetaClass


class ErrorState(State):
    """ Represents a state of the system when it behaves abnormally """


class ErrorTransition(Transition):
    """ Base class for managing a tranition of the system into the ErrorState. All error logging should be done here """
    target_state = ErrorState

    def __init__(self, system, error):
        super(ErrorTransition, self).__init__(system)
        self._error = error

    @abstractmethod
    def move(self):
        pass


def _get_cost(states):
    """ Returns a cumulative cost of the whole chain of transformations """
    cost = 0
    cursor = states[0]
    for state in states[1:]:
        cost += cursor.transition_map[state].cost
        cursor = state
    return cost


def _find_shortest_path(graph, start, end, path=[]):
    """ Derived from: https://www.python.org/doc/essays/graphs/

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
    """ The crawler responsible for orchestrating the transitions of system's states """

    def __init__(self, system, initial_transition, error_handling_transition):
        """
        @system: system under testing. All transition shall change its state.
        @initial_transition: a special transformation that configures the system to a blank state.
                             Note: it must be possible to perform the transition at any point. I.e. all the states
                             should be transitionable to the initial state. It might me the most expensive
                             transition in the system.
        @error_handling_transition: subclass of ErrorTransition
        """
        self._system = system
        self._current_state = None
        self._initial_transition = initial_transition
        self._initial_state = initial_transition.target_state
        self._error_handling_transition = error_handling_transition
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
        return self._current_state

    def move(self, state):
        """ Attempts to make a move to another state """
        if state is self._current_state:
            return
        if state is self._initial_state or self._current_state is None:
            self._initial_transition(self._system).move()
            self._current_state = self._initial_state
            if state is self._initial_state:
                return
        shortest_path = _find_shortest_path(self._state_graph, self._current_state, state)
        if shortest_path is None:
            raise StateMachineCrawlerError("There is no way to achieve state %r" % state)
        print shortest_path
        for next_state in shortest_path[1:]:
            transition = self._current_state.transition_map[next_state]
            try:
                transition(self._system).move()
                self._current_state = next_state
            except Exception, error:
                error_transition = self._error_handling_transition(self._system, error)
                error_transition.move()
                self.move(self._initial_state)
                break
