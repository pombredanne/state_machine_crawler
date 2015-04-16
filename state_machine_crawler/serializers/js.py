import json


class Serializer(object):
    mimetype = "application/json"

    def __init__(self, scm):
        self._scm = scm

    def __repr__(self):
        rval = []
        for source_state, target_states in self._scm._state_graph.iteritems():
            state_info = {
                "name": source_state.full_name,
                "visited": source_state in self._scm._visited_states,
                "failed": source_state in self._scm._error_states
            }

            transitions = []
            for target_state in target_states:
                transitions.append({
                    "target": target_state.full_name,
                    "visited": (source_state, target_state) in self._scm._visited_transitions,
                    "failed": (source_state, target_state) in self._scm._error_transitions,
                })

            state_info["transitions"] = transitions
            rval.append(state_info)
        return json.dumps(rval)
