import pydot

from .dot import Serializer as DotSerializer


class Serializer(object):
    mimetype = "image/svg+xml"

    def __init__(self, scm):
        self._dot_serializer = DotSerializer(scm)

    def __repr__(self):
        dot = repr(self._dot_serializer)
        graph = pydot.graph_from_dot_data(dot)
        return graph.create_svg()
