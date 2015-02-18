import logging
import re
from collections import defaultdict

from .errors import TransitionError, DeclarationError
from .blocks import State


LOG = logging.getLogger("state_machine_crawler")

ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter("%(message)s"))

LOG.addHandler(ch)

NODE_TPL = "%(name)s [style=filled label=\"%(label)s\" shape=%(shape)s fillcolor=%(color)s fontcolor=%(text_color)s];"
EDGE_TPL = "%(source)s -> %(target)s [color=%(color)s fontcolor=%(text_color)s label=\"%(label)s\"];"


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

        def verify(self):  # pragma: no cover
            return True

    def __init__(self, system, initial_state):
        if not issubclass(initial_state, State):
            raise DeclarationError("%r is not a State subclass" % initial_state)
        self.clear()
        self._system = system
        self._initial_state = initial_state
        self._state_graph = the_map = _create_transition_map(self._initial_state)

        for target_states in the_map.itervalues():
            target_states.add(self._initial_state)

        self._state_graph[self.EntryPoint] = {self._initial_state}
        self._current_state = self._entry_point = self.EntryPoint

        LOG.info("State machine crawler initialized")

    def clear(self):
        self._current_transition = None
        self._error_states = set()
        self._visited_states = set()
        self._visited_transitions = set()
        self._error_transitions = set()

    @property
    def state(self):
        """ Represents a current state of the sytstem """
        return self._current_state

    def _err(self, target_state, msg):
        raise TransitionError("Move from state %r to state %r has failed: %s" % (self._current_state,
                                                                                 target_state, msg))

    def _do_step(self, next_state):
        self._next_state = next_state
        self._current_transition = transition = self._get_transition(self._current_state, next_state)
        try:
            LOG.info("Transition to state %s started", next_state)
            transition(transition.im_class(self._system))
            LOG.info("Transition to state %s finished", next_state)
            transition_ok = True
        except Exception:
            self._error_transitions.add(transition)
            self._error_states.add(next_state)
            LOG.exception("Failed to move to: %s", next_state)
            transition_ok = False
        self._visited_transitions.add(transition)
        if not transition_ok:
            self._current_state = self._entry_point
            self._err(next_state, "transition failure")
        try:
            LOG.info("Verification of state %s started", next_state)
            verification_ok = next_state(self._system).verify()
            LOG.info("Verification of state %s finished", next_state)
        except Exception:
            LOG.exception("Failed to verify transition to: %s" % next_state)
            verification_ok = False
        if verification_ok:
            self._current_state = next_state
            LOG.info("State changed to %s", next_state)
            self._visited_states.add(next_state)
            self._current_transition = None
            self._next_state = None
        else:
            self._current_transition = None
            self._next_state = None
            self._error_states = _get_all_unreachable_nodes(self._state_graph, self._entry_point,
                                                            set.union(self._error_states, {next_state}),
                                                            self._transition_exclusion_list)

            # mark all outgoing transitions from error states as impossible
            for state in self._error_states:
                for transition in state.transition_map.itervalues():
                    self._error_transitions.add(transition)

            LOG.error("State verification error for: %s", next_state)
            self._current_state = self._entry_point
            self._err(next_state, "verification failure")

    def _get_transition(self, source_state, target_state):
        if target_state is self._initial_state:
            return self.EntryPoint.transition_map[target_state]
        else:
            return source_state.transition_map[target_state]

    @property
    def _transition_exclusion_list(self):
        transition_exclusion_list = set()
        for transition in self._error_transitions:
            transition_exclusion_list.add((transition.source_state, transition.target_state))
        return transition_exclusion_list

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
        reachable_state_graph = _create_transition_map_with_exclusions(self._state_graph,
                                                                       self._entry_point,
                                                                       self._error_states,
                                                                       self._transition_exclusion_list)
        shortest_path = _find_shortest_path(reachable_state_graph, self._current_state, state, get_cost=self._get_cost)
        if shortest_path is None:
            raise TransitionError("There is no way to achieve state %r" % state)
        if state is self._current_state:
            next_states = [state]
        else:
            next_states = shortest_path[1:]
        for next_state in next_states:
            self._do_step(next_state)

    def verify_all_states(self, pattern=None):
        """
        Makes sure that all states can be visited. It uses a depth first search to find the somewhat the quickest path.

        @pattern (str=None): visits only the states full names of which match the pattern
        """
        all_states_to_check = _dfs(self._state_graph, self._initial_state)

        actual_states_to_check = []
        if pattern is not None:
            for state in all_states_to_check:
                if re.match(pattern, state.full_name):
                    actual_states_to_check.append(state)
        else:
            actual_states_to_check = all_states_to_check

        for state in actual_states_to_check:
            if state in self._error_states or state in self._visited_states:  # pragma: no cover
                continue
            try:
                self.move(state)
            except TransitionError:
                pass  # we just move on
        if self._initial_state not in self._error_states:
            self.move(self._initial_state)
            self._current_state = self._entry_point
        if self._error_states:
            failed_states = map(str, self._error_states)
            raise TransitionError("Failed to visit the following states: %s" % ", ".join(sorted(failed_states)))

    def _serialize_state(self, state):  # pragma: no cover
        if state is self._entry_point:
            shape = "doublecircle"
            label = "+"
        else:
            shape = "box"
            label = state.__name__
        if state is self._current_state:
            color = "forestgreen"
            text_color = "white"
        elif state is self._next_state:
            color = "darkkhaki"
            text_color = "black"
        elif state in self._error_states:
            if state in self._visited_states:
                color = "orange"
            else:
                color = "red"
            text_color = "black"
        elif state in self._visited_states:
            color = "yellow"
            text_color = "black"
        else:
            color = "white"
            text_color = "black"
        return NODE_TPL % dict(name=state.__name__, label=label, shape=shape, color=color, text_color=text_color)

    def _serialize_transition(self, transition):  # pragma: no cover
        if filter(lambda error_transition: _equivalent(transition, error_transition), self._error_transitions):
            color = text_color = "red"
        elif _equivalent(transition, self._current_transition):
            color = text_color = "forestgreen"
        elif transition in self._visited_transitions:
            color = "yellow"
            text_color = "black"
        else:
            color = text_color = "black"

        if transition.cost == 1:
            label = " "
        else:
            label = "$%d" % transition.cost

        if transition.source_state is None:
            source_state = transition.im_class.__name__
        else:
            source_state = transition.source_state.__name__

        if transition.target_state in [None, "self"]:
            target_state = transition.im_class.__name__
        else:
            target_state = transition.target_state.__name__

        return EDGE_TPL % dict(source=source_state,
                               target=target_state,
                               color=color,
                               label=label,
                               text_color=text_color)

    def __repr__(self):
        # TODO: implement .dot graph generation here without pydot dependency
        all_states = set()
        for source_state, target_states in self._state_graph.iteritems():
            all_states.add(source_state)
            for st in target_states:
                all_states.add(st)

        module_map = defaultdict(list)
        for state in all_states:
            if state is self._entry_point:
                continue
            module_map[state.__module__].append(state)

        rval = ["digraph StateMachine {splines=polyline; concentrate=true; rankdir=LR;"]

        rval.append(self._serialize_state(self._entry_point))

        i = 1
        for module_name, states in module_map.iteritems():
            cluster_name = module_name.split(".")[-1]
            cluster_data = ["subgraph cluster_%d {label=\"%s\";color=blue;fontcolor=blue;" % (i, cluster_name)]
            for state in states:
                cluster_data.append(self._serialize_state(state))
            cluster_data.append("}")
            rval.append("".join(cluster_data))
            i += 1

        for state in all_states:
            for transition in state.transition_map.itervalues():
                rval.append(self._serialize_transition(transition))

        rval.append("}")

        return "".join(rval)
