class Serializer(object):
    mimetype = "text/plain"

    def __init__(self, scm):
        self._scm = scm

    def __repr__(self):
        rval = ["State machine status: "]

        state_count = len(self._scm._state_graph)
        transition_count = 0
        for source_state, target_states in self._scm._state_graph.iteritems():
            transition_count += len(target_states)

        error_state_count = len(self._scm._error_states)
        visited_state_count = len(self._scm._visited_states)
        error_transition_count = len(self._scm._error_transitions)
        visited_transition_count = len(self._scm._visited_transitions)

        rval.append("States: [T=%d, V=%d, E=%d]" % (state_count, visited_state_count, error_state_count))
        rval.append("Transitions: [T=%d, V=%d, E=%d]" % (transition_count, visited_transition_count,
                                                         error_transition_count))

        rval.append("Failed states: %r" % self._scm._error_states)
        rval.append("Failed transitions: %r" % self._scm._error_transitions)

        return "\n".join(rval) + "\n"
