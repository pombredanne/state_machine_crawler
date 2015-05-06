import json


class Serializer(object):
    mimetype = "application/json"

    def __init__(self, scm):
        self._scm = scm

    def __repr__(self):
        rval = []

        all_states = set()
        for source_state, target_states in self._scm._state_graph.iteritems():
            all_states.add(source_state)
            for st in target_states:
                all_states.add(st)

        for source_state in all_states:
            state_info = {
                "name": source_state.full_name,
                "current": source_state is self._scm._current_state,
                "next": source_state is self._scm._next_state,
                "visited": source_state in self._scm._visited_states,
                "failed": source_state in self._scm._error_states
            }

            transitions = []
            for target_state, transition in source_state.transition_map.iteritems():
                transitions.append({
                    "cost": transition.cost,
                    "target": target_state.full_name,
                    "visited": (source_state, target_state) in self._scm._visited_transitions,
                    "failed": (source_state, target_state) in self._scm._error_transitions,
                })

            state_info["transitions"] = transitions
            rval.append(state_info)
        return json.dumps(rval)
