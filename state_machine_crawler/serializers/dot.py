from .hierarchy import create_hierarchy, get_all_transitions
from ..blocks import State
from ..state_machine_crawler import StateMachineCrawler


NODE_TPL = "%(name)s [style=filled label=\"%(label)s\" shape=%(shape)s fillcolor=%(color)s fontcolor=%(text_color)s];"
EDGE_TPL = "%(source)s -> %(target)s [color=%(color)s fontcolor=%(text_color)s label=\"%(label)s\"];"


def node_id(name):
    return name.strip().replace(".", "_").replace(" ", "_")


def serialize_state(state):
    if state["_entry"] is StateMachineCrawler.EntryPoint:
        shape = "doublecircle"
        label = "+"
    else:
        shape = "box"
        label = state["name"].split(".")[-1]
    if state["current"]:
        color = "blue"
        text_color = "white"
    elif state["next"]:
        color = "dodgerblue"
        text_color = "black"
    elif state["failed"]:
        if state["visited"]:
            color = "orange"
        else:
            color = "red"
        text_color = "black"
    elif state["visited"]:
        color = "forestgreen"
        text_color = "white"
    else:
        color = "white"
        text_color = "black"

    return NODE_TPL % dict(
        name=node_id(state["name"]),
        label=label,
        shape=shape,
        color=color,
        text_color=text_color)


def serialize_transition(transition):
    if transition["failed"]:
        if transition["visited"]:
            color = text_color = "orange"
        else:
            color = text_color = "red"
    elif transition["current"]:
        color = text_color = "blue"
    elif transition["visited"]:
        color = text_color = "forestgreen"
    else:
        color = text_color = "black"

    if transition["cost"] == 1:
        label = " "
    else:
        label = "$%d" % transition["cost"]

    return EDGE_TPL % dict(source=node_id(transition["source"]),
                           target=node_id(transition["target"]),
                           color=color,
                           label=label,
                           text_color=text_color)


class Serializer(object):
    mimetype = "application/dot"

    def __init__(self, scm):
        self._scm = scm
        self._cluster_index = 0

    def _serialize_collection(self, hierarchy, cluster_name=None):
        self._cluster_index += 1
        if cluster_name:
            rval = ["subgraph cluster_%d {label=\"%s\";color=blue;fontcolor=blue;" % (self._cluster_index,
                                                                                      cluster_name)]
        else:
            rval = []

        for node_name, node_value in hierarchy.iteritems():
            if isinstance(node_value, dict):
                if "_entry" in node_value and issubclass(node_value["_entry"], State):
                    rval.append(serialize_state(node_value))
                else:
                    rval.extend(self._serialize_collection(node_value, node_name))

        if cluster_name:
            rval.append("}")

        return rval

    def __repr__(self):
        graph = self._scm.as_graph()

        rval = ["digraph StateMachine {splines=polyline; concentrate=true; rankdir=LR;"]

        hierarchy = create_hierarchy(graph)

        entry_point = hierarchy.pop("state_machine_crawler")["state_machine_crawler"]["EntryPoint"]
        rval.extend(serialize_state(entry_point))

        rval.extend(self._serialize_collection(hierarchy))

        for transition in get_all_transitions(graph):
            rval.append(serialize_transition(transition))

        rval.append("}")

        return "".join(rval)
