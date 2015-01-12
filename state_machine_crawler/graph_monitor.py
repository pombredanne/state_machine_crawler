import time
import threading

import pydot

from .real_time_image_viewer import run_viewer, StatusObject


class GraphMonitor(object):

    def __init__(self, title, crawler):
        self._status = StatusObject()
        self._status.alive = False
        self._refresher_thread = threading.Thread(target=self._run_graph_refresher)
        self._viewer_thread = threading.Thread(target=run_viewer, args=(title + ".png", self._status))
        self.crawler = crawler  # intentionally public
        self._refresher_check_time = time.time()
        self._title = title

    def _set_node(self, state, current_state):
        source_node = pydot.Node(state.__name__)
        source_node.set_style("filled")
        color = "red" if state is current_state else "white"
        source_node.set_fillcolor(color)
        source_node.set_shape("box")
        self._graph.add_node(source_node)

    def _set_edge(self, transition, current_transition):
        if not transition.source_state:
            return
        edge = pydot.Edge(transition.source_state.__name__, transition.target_state.__name__)
        style = "bold" if transition is self.crawler._initial_transition else "dashed"
        color = "red" if transition is current_transition else "darkorchid4"
        edge.set_color(color)
        edge.set_style(style)
        edge.set_fontcolor(color)
        edge.set_label(transition.__name__)
        self._graph.add_edge(edge)

    def _gen_graph(self, source_state, cur_state, cur_transition):
        for target_state, transition in source_state.transition_map.iteritems():
            if transition in self._processed_transitions:
                continue
            self._processed_transitions.add(transition)
            self._set_node(target_state, cur_state)
            self._set_edge(transition, cur_transition)
            self._gen_graph(target_state, cur_state, cur_transition)

    def save(self):
        self._processed_transitions = set()
        self._graph = pydot.Dot(self._title, graph_type='digraph')
        self._graph.set_splines("polyline")
        self._gen_graph(self.crawler._initial_state, self.crawler._current_state, self.crawler._current_transition)
        self._graph.write_png(self._title + ".png")

    def _run_graph_refresher(self):
        while self._status.alive:
            now = time.time()
            if self._refresher_check_time + 0.5 < now:
                self._refresher_check_time = now
                self.save()

    def start(self):
        if self._status.alive:
            return
        if not self.crawler:
            return
        self._status.alive = True
        self._refresher_thread.start()
        self._viewer_thread.start()

    def stop(self):
        if not self._status.alive:
            return
        self._status.alive = False
        self._refresher_thread.join()
        self._viewer_thread.join()
