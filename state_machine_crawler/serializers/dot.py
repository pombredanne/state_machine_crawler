from collections import defaultdict

NODE_TPL = "%(name)s [style=filled label=\"%(label)s\" shape=%(shape)s fillcolor=%(color)s fontcolor=%(text_color)s];"
EDGE_TPL = "%(source)s -> %(target)s [color=%(color)s fontcolor=%(text_color)s label=\"%(label)s\"];"


class Serializer(object):
    mimetype = "application/dot"

    def __init__(self, scm):
        self._scm = scm

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
        return NODE_TPL % dict(name=state.full_name, label=label, shape=shape, color=color, text_color=text_color)

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

        return EDGE_TPL % dict(source=source_state.full_name,
                               target=target_state.full_name,
                               color=color,
                               label=label,
                               text_color=text_color)

    def __repr__(self):
        # TODO: implement .dot graph generation here without pydot dependency
        all_states = set()
        for source_state, target_states in self._scm._state_graph.iteritems():
            all_states.add(source_state)
            for st in target_states:
                all_states.add(st)

        module_map = defaultdict(list)
        for state in all_states:
            if state is self._scm.EntryPoint:
                continue
            module_map[state.__module__].append(state)

        rval = ["digraph StateMachine {splines=polyline; concentrate=true; rankdir=LR;"]

        rval.append(self._serialize_state(self._scm.EntryPoint))

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
            for target_state, transition in state.transition_map.iteritems():
                rval.append(self._serialize_transition(state, target_state, transition.cost))

        rval.append("}")

        return "".join(rval)
