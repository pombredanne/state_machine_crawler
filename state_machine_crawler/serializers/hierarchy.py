def create_hierarchy(scm):
    """ Creates a cluster hiearachy from the state machine """
    root = {}

    for name, state in scm._state_name_map.iteritems():
        parent_result = local_result = root
        nodes = name.split(".")
        for node in nodes:
            parent_result = local_result
            local_result = local_result.setdefault(node, {})
        parent_result[nodes[-1]] = state

    return root
