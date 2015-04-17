import re

from .errors import TransitionError, DeclarationError, UnreachableStateError
from .blocks import State
from .logger import StateLogger


def _equivalent(transition_one, transition_two):
    if not (transition_one and transition_two):
        return False
    p1 = transition_one.source_state == transition_two.source_state
    p2 = transition_one.target_state == transition_two.target_state
    p3 = transition_one.im_class == transition_two.im_class
    return p1 and p2 and p3


def _find_shortest_path(graph, start, end, path=[], get_cost=len):
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


def _create_transition_map(state, state_map=None):
    """ Returns a graph for state transitioning """
    state_map = state_map or {}
    if state in state_map:
        return state_map
    state_map[state] = child_states = set()
    for next_state in state.transition_map.keys():
        child_states.add(next_state)
        _create_transition_map(next_state, state_map)
    return state_map


def _create_transition_map_with_exclusions(graph, entry_point, state_exclusion_list=None,
                                           transition_exclusion_list=None,
                                           filtered_graph=None):
    """ Creates a sub_graph of a @graph with an assumption that a bunch of nodes from @state_exclusion_list are not
    reachable
    """
    filtered_graph = filtered_graph or {}
    state_exclusion_list = state_exclusion_list or []
    transition_exclusion_list = transition_exclusion_list or []
    if entry_point in state_exclusion_list:
        return {}
    if entry_point in filtered_graph or entry_point not in graph:
        return filtered_graph
    filtered_graph[entry_point] = filtered_children = set()
    for child_node in graph[entry_point]:
        if (entry_point, child_node) in transition_exclusion_list:
            continue
        if _create_transition_map_with_exclusions(graph, child_node, state_exclusion_list, transition_exclusion_list,
                                                  filtered_graph):
            filtered_children.add(child_node)
    return filtered_graph


def _get_missing_nodes(graph, sub_graph, entry_point):
    """ Returns a set of nodes that are present in the @graph but are missing in the @sub_graph """
    all_nodes = set()

    def _add_nodes(parent):
        if parent in all_nodes:
            return
        all_nodes.add(parent)
        for child in graph.get(parent, []):
            _add_nodes(child)

    def _remove_nodes(parent):
        if parent not in all_nodes:
            return
        all_nodes.remove(parent)
        for child in sub_graph.get(parent, []):
            _remove_nodes(child)

    _add_nodes(entry_point)
    _remove_nodes(entry_point)

    return all_nodes


def _dfs(graph, start, visited=None):
    """ Recursive depth first search """
    visited = visited or []
    if start not in visited:
        visited.append(start)
    for node in set(graph[start]) - set(visited):
        _dfs(graph, node, visited)
    return visited


def _get_all_unreachable_nodes(graph, entry_point, state_exclusion_list, transition_exclusion_list):
    """ Given a @graph and a bunch of unreachable states in @state_exclusion_list calculates which other nodes cannot
    be reached
    """
    sub_graph = _create_transition_map_with_exclusions(graph, entry_point, state_exclusion_list,
                                                       transition_exclusion_list)
    return _get_missing_nodes(graph, sub_graph, entry_point)


class StateMachineCrawler(object):
    """ The crawler is responsible for orchestrating the transitions of system's states

    system
        All transitions shall change the internal state of this object.
    initial_state
        The first real state of the system. It must define a transition from the StateMachineCrawler.EntryPoint
        otherwise the crawler won't be able to find its way through

    >>> scm = StateMachineCrawler(system_object, InitialState)
    """

    class EntryPoint(State):

        def verify(self):
            return True

    def __init__(self, system, initial_state):
        if not issubclass(initial_state, State):
            raise DeclarationError("%r is not a State subclass" % initial_state)
        self.clear()
        self._system = system
        self._initial_state = initial_state
        self._state_graph = the_map = _create_transition_map(self._initial_state)

        for target_states in the_map.itervalues():
            target_states.add(self.EntryPoint)

        self._state_graph[self.EntryPoint] = {self._initial_state}
        self._current_state = self.EntryPoint
        self.log = StateLogger()

    def clear(self):
        self._error_states = set()
        self._visited_states = set()
        self._visited_transitions = set()
        self._error_transitions = set()
        self._visited_states.add(self.EntryPoint)
        self._history = []

    @property
    def state(self):
        """ Represents a current state of the sytstem """
        return self._current_state

    def _err(self, target_state, msg):
        text = "Move from state %r to state %r has failed: %s." % (self._current_state, target_state, msg)
        text += "\nHistory: \n%s\n" % " -> ".join([hist.full_name for hist in self._history])
        raise TransitionError(text)

    def _do_step(self, next_state):
        if self._current_state is self.EntryPoint:
            self._history = []
        self._next_state = next_state
        transition = self._get_transition(self._current_state, next_state)
        self.log.msg(self._current_state, self._next_state)
        self.log.transition()
        try:
            transition(transition.im_class(self._system))
            self._visited_transitions.add((self._current_state, next_state))
            transition_ok = True
            self.log.ok()
        except Exception:
            self._error_transitions.add((self._current_state, next_state))
            transition_ok = False
            self.log.nok()
            self.log.show_traceback()
        if not transition_ok:
            self._error_states = _get_all_unreachable_nodes(self._state_graph, self.EntryPoint,
                                                            set.union(self._error_states, {next_state}),
                                                            self._error_transitions)
            self._current_state = self.EntryPoint
            self._err(next_state, "transition failure")
        self.log.verification()
        try:
            next_state(self._system).verify()
            self.log.ok()
            self._current_state = next_state
            self._history.append(next_state)
            self._visited_states.add(next_state)
            self._next_state = None
        except Exception:
            self.log.nok()
            self.log.show_traceback()
            self._next_state = None
            self._error_states = _get_all_unreachable_nodes(self._state_graph, self.EntryPoint,
                                                            set.union(self._error_states, {next_state}),
                                                            self._error_transitions)

            # mark all outgoing transitions from error states as impossible
            for state in self._error_states:
                for transition in state.transition_map.itervalues():
                    self._error_transitions.add((state, transition.target_state))

            self._current_state = self.EntryPoint
            self._err(next_state, "verification failure")

    def _get_transition(self, source_state, target_state):
        if target_state is self.EntryPoint:
            def tempo(ep_instance):
                pass
            tempo.cost = 0
            tempo.target_state = target_state
            tempo.source_state = source_state
            tempo.im_class = source_state
            return tempo
        else:
            return source_state.transition_map[target_state]

    def _get_cost(self, states):
        """ Returns a cumulative cost of the whole chain of transitions """
        cost = 0
        cursor = states[0]
        for state in states[1:]:
            cost += self._get_transition(cursor, state).cost
            cursor = state
        return cost

    def move(self, state):
        """ Performs a transition from the current state to the state passed as an argument

        state (subclass of :class:`State <state_machine_crawler.State>`)
            target state of the system

        >>> scm.move(StateOne)
        >>> scm.state is StateOne
        True
        """
        if state is self.EntryPoint:
            self._next_state = None
            self._current_state = self.EntryPoint
            return
        reachable_state_graph = _create_transition_map_with_exclusions(self._state_graph,
                                                                       self.EntryPoint,
                                                                       self._error_states,
                                                                       self._error_transitions)
        shortest_path = _find_shortest_path(reachable_state_graph, self._current_state, state, get_cost=self._get_cost)
        if shortest_path is None:
            raise UnreachableStateError("There is no way to achieve state %r" % state)
        if state is self._current_state:
            next_states = [state]
        else:
            next_states = shortest_path[1:]
        for next_state in next_states:
            self._do_step(next_state)

    def verify_all_states(self, pattern=None, full=False):
        """
        Makes sure that all states can be visited. It uses a depth first search to find the somewhat the quickest path.

        @pattern (str=None): visits only the states full names of which match the pattern
        @full (bool=False): if True, not only all states are visited but also all transitions are exercised
        """
        all_states_to_check = _dfs(self._state_graph, self._initial_state)

        actual_states_to_check = []
        if pattern is not None:
            for state in all_states_to_check:
                if re.match(pattern, state.full_name):
                    actual_states_to_check.append(state)
        else:
            actual_states_to_check = all_states_to_check

        def _handled_call(function):
            try:
                function()
            except TransitionError, e:
                self.log.err(e)
            except UnreachableStateError:  # pragma: no cover
                pass  # show must go on!

        for state in actual_states_to_check:
            if state in self._error_states or state in self._visited_states:
                continue
            _handled_call(lambda: self.move(state))

        if full:

            unexecuted_transitions = set()
            for source_state, target_states in self._state_graph.iteritems():
                for target_state in target_states:
                    transition = (source_state, target_state)
                    if transition not in set.union(self._error_transitions, self._visited_transitions):
                        if target_state is self.EntryPoint:
                            continue
                        if pattern and not (re.match(pattern, source_state.full_name) and
                                            re.match(pattern, target_state.full_name)):
                            continue
                        unexecuted_transitions.add(transition)

            # TODO: find the most optimal way to execute the rest of transitions

            for transition in unexecuted_transitions:

                def _call():
                    if transition[0] != self._current_state:
                        self.move(transition[0])
                    self._do_step(transition[1])

                _handled_call(_call)

        self.move(self.EntryPoint)
        if self._error_states:
            failed_states = map(str, self._error_states)
            raise TransitionError("Failed to visit the following states: %s" % ", ".join(sorted(failed_states)))
