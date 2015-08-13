from collections import defaultdict


def create_hierarchy(graph):
    states = defaultdict(dict)
    for key, value in graph.iteritems():
        cursor = states
        nodes = key.split(".")
        parents = nodes[:-1]
        item = nodes[-1]

        for node in parents:
            cursor[node] = cursor.get(node, {})
            cursor = cursor[node]

        cursor[item] = value

    return states


def get_all_transitions(graph):
    transitions = []
    for val in graph.itervalues():
        transitions.extend(val["transitions"].values())
    return transitions
