from .hierarchy import create_hierarchy
from ..blocks import State


NODE_TPL = "%(name)s [style=filled label=\"%(label)s\" shape=%(shape)s fillcolor=%(color)s fontcolor=%(text_color)s];"
EDGE_TPL = "%(source)s -> %(target)s [color=%(color)s fontcolor=%(text_color)s label=\"%(label)s\"];"


class Serializer(object):
    mimetype = "application/dot"

    def __init__(self, scm):
        self._scm = scm
        self._cluster_index = 0

    def _serialize_state(self, state):  # pragma: no cover
        if state is self._scm.EntryPoint:
            shape = "doublecircle"
            label = "+"
        else:
            shape = "box"
            label = state.__name__
        if state is self._scm._current_state:
            color = "blue"
            text_color = "white"
        elif state is self._scm._next_state:
            color = "dodgerblue"
            text_color = "black"
        elif state in self._scm._error_states:
            if state in self._scm._visited_states:
                color = "orange"
            else:
                color = "red"
            text_color = "black"
        elif state in self._scm._visited_states:
            color = "forestgreen"
            text_color = "white"
        else:
            color = "white"
            text_color = "black"
        return NODE_TPL % dict(
            name=state.full_name.replace(".", "_"),
            label=label,
            shape=shape,
            color=color,
            text_color=text_color)

    def _serialize_transition(self, source_state, target_state, cost):  # pragma: no cover
        if (source_state, target_state) in self._scm._error_transitions or source_state in self._scm._error_states or \
                target_state in self._scm._error_states:
            if (source_state, target_state) in self._scm._visited_transitions:
                color = text_color = "orange"
            else:
                color = text_color = "red"
        elif self._scm._current_state is source_state and self._scm._next_state is target_state:
            color = text_color = "blue"
        elif (source_state, target_state) in self._scm._visited_transitions:
            color = text_color = "forestgreen"
        else:
            color = text_color = "black"

        if cost == 1:
            label = " "
        else:
            label = "$%d" % cost

        return EDGE_TPL % dict(source=source_state.full_name.replace(".", "_"),
                               target=target_state.full_name.replace(".", "_"),
                               color=color,
                               label=label,
                               text_color=text_color)

    def _serialize_collection(self, module_map, cluster_name=None):
        self._cluster_index += 1
        if cluster_name:
            rval = ["subgraph cluster_%d {label=\"%s\";color=blue;fontcolor=blue;" % (self._cluster_index,
                                                                                      cluster_name)]
        else:
            rval = []

        for node_name, node_value in module_map.iteritems():
            if isinstance(node_value, dict):
                rval.extend(self._serialize_collection(node_value, node_name))
            elif issubclass(node_value, State):
                rval.append(self._serialize_state(node_value))

        if cluster_name:
            rval.append("}")

        return rval

    def __repr__(self):
        # TODO: implement .dot graph generation here without pydot dependency
        all_states = set()
        for source_state, target_states in self._scm._state_graph.iteritems():
            all_states.add(source_state)
            for st in target_states:
                all_states.add(st)

        rval = ["digraph StateMachine {splines=polyline; concentrate=true; rankdir=LR;"]

        rval.append(self._serialize_state(self._scm.EntryPoint))

        rval.extend(self._serialize_collection(create_hierarchy(self._scm)))

        for key, transition in self._scm._transition_map.iteritems():
            state, target_state = key
            if target_state is not self._scm.EntryPoint:
                rval.append(self._serialize_transition(state, target_state, transition.cost))

        rval.append("}")

        return "".join(rval)
