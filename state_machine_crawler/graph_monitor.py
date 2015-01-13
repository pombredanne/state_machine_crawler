import time
import threading
import os
from Tkinter import PhotoImage, Tk, Canvas, VERTICAL, HORIZONTAL, BOTTOM, RIGHT, LEFT, Y, X, BOTH, Scrollbar

import pydot


class StatusObject:

    def __init__(self):
        self.alive = True


def run_viewer(file_name, status_object=None):

    status_object = status_object or StatusObject()

    viewer = Tk()
    viewer.title(file_name)

    while not os.path.exists(file_name):
        if status_object.alive:
            continue
        else:
            return

    ok = False

    while not ok:
        if not status_object.alive:
            return
        try:
            img = PhotoImage(file=file_name)
            ok = True
        except:
            pass

    canvas = Canvas(viewer, width=min(img.width(), 1024), heigh=min(img.height(), 768),
                    scrollregion=(0, 0, img.width(), img.height()))

    hbar = Scrollbar(viewer, orient=HORIZONTAL)
    hbar.config(command=canvas.xview)

    vbar = Scrollbar(viewer, orient=VERTICAL)
    vbar.config(command=canvas.yview)

    image_on_canvas = canvas.create_image(img.width() / 2, img.height() / 2, image=img)
    canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)

    hbar.pack(side=BOTTOM, fill=X)
    vbar.pack(side=RIGHT, fill=Y)
    canvas.pack(side=LEFT, expand=True, fill=BOTH)

    def _refresh_viewer():
        try:
            refreshed_photo = PhotoImage(file=file_name)
            canvas.itemconfig(image_on_canvas, image=refreshed_photo)
            canvas.img = refreshed_photo
        except:
            pass

    def loop():
        _refresh_viewer()
        if not status_object.alive:
            viewer.quit()
            return
        viewer.after(50, loop)

    loop()
    viewer.mainloop()


class GraphMonitor(object):
    """ A Tkinter based monitor for StateMachineCrawler. Shows a Graphviz diagram with all the states and marks the
    current state of the system on the diagram.

    title
        A human readable name of the graph to be shown
    crawler
        StateMachineCrawler instance

    >>> crawler = StateMachineCrawler(system=..., _initial_transition=...)
    >>> monitor = GraphMonitor("state_graph", crawler)
    >>> monitor.start()
    >>> ...
    >>> monitor.stop()
    """

    def __init__(self, title, crawler):
        self._status = StatusObject()
        self._status.alive = False
        self._refresher_thread = threading.Thread(target=self._run_graph_refresher)
        self._viewer_thread = threading.Thread(target=run_viewer, args=(title + ".png", self._status))
        self.crawler = crawler  # intentionally public
        self._refresher_check_time = time.time()
        self._title = title

    @property
    def _can_be_started(self):
        if not os.environ.get("DISPLAY", False):
            print "Display is not available"
            return False
        elif not pydot.find_graphviz():
            print "Graphviz is not available"
            return False
        else:
            return True

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

    def _save(self):
        self._processed_transitions = set()
        self._graph = pydot.Dot(self._title, graph_type='digraph')
        self._graph.set_splines("polyline")
        self._gen_graph(self.crawler._initial_state, self.crawler._current_state, self.crawler._current_transition)
        self._graph.write_png(self._title + ".png")

    def _run_graph_refresher(self):
        while self._status.alive:
            now = time.time()
            if self._refresher_check_time + 0.2 < now:
                self._save()
                self._refresher_check_time = time.time()

    def start(self):
        """ Launches the monitor in a separate thread """
        if not self._can_be_started:
            return
        if self._status.alive:
            return
        if not self.crawler:
            return
        self._status.alive = True
        self._refresher_thread.start()
        self._viewer_thread.start()

    def stop(self):
        """ Stops the monitor """
        if not self._status.alive:
            return
        self._status.alive = False
        self._refresher_thread.join()
        self._viewer_thread.join()
