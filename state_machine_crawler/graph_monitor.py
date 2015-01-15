import threading
import os
from Tkinter import PhotoImage, Tk, Canvas, VERTICAL, HORIZONTAL, BOTTOM, RIGHT, LEFT, Y, X, BOTH, Scrollbar, NW, \
    CURRENT

import pydot


class StatusObject:

    def __init__(self):
        self.alive = True


def abs_val(value, limit):
    if value > limit:
        return limit
    if value < limit:
        return value
    return limit


class GraphViewer(object):

    def __init__(self, file_name, status_object=None):
        self._file_name = file_name
        self._status_object = status_object or StatusObject()
        self._main_window = mw = Tk()
        mw.title(file_name)
        self._zoom_ratio = 1
        self._img = img = self._create_image()
        if img is None:
            return
        self._canvas = canvas = Canvas(mw, width=abs_val(img.width(), 1024), heigh=abs_val(img.height(), 768),
                                       scrollregion=(0, 0, img.width(), img.height()))

        self._hbar = hbar = Scrollbar(mw, orient=HORIZONTAL)
        hbar.config(command=canvas.xview)

        self._vbar = vbar = Scrollbar(mw, orient=VERTICAL)
        vbar.config(command=canvas.yview)

        self._image_on_canvas = canvas.create_image(0, 0, image=img, anchor=NW)
        canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)

        hbar.pack(side=BOTTOM, fill=X)
        vbar.pack(side=RIGHT, fill=Y)
        canvas.pack(side=LEFT, expand=True, fill=BOTH)

        canvas.bind_all('<4>', self._zoomIn, add='+')
        canvas.bind_all('<5>', self._zoomOut, add='+')
        canvas.tag_bind(CURRENT, "<Button-1>", self._click)
        canvas.tag_bind(CURRENT, "<B1-Motion>", self._move)
        canvas.focus_set()

        self._reload()
        mw.mainloop()

    def _create_image(self):
        while not os.path.exists(self._file_name):
            if self._status_object.alive:
                continue
            else:
                return

        while True:
            if not self._status_object.alive:
                return
            try:
                return PhotoImage(file=self._file_name)
            except:
                pass

    def _update_scroll_area(self):
        self._canvas.configure(scrollregion=(0, 0, self._img.width(), self._img.height()))

    def _zoom(self, event, prev_zoom):
        self._img.subsample(self._zoom_ratio)
        self._update_scroll_area()

    def _zoomIn(self, event):
        prev_zoom = self._zoom_ratio
        self._zoom_ratio = max(1, self._zoom_ratio - 1)
        self._zoom(event, prev_zoom)

    def _zoomOut(self, event):
        prev_zoom = self._zoom_ratio
        self._zoom_ratio = max(1, self._zoom_ratio + 1)
        self._zoom(event, prev_zoom)

    def _click(self, event):
        self._canvas.scan_mark(event.x, event.y)

    def _move(self, event):
        self._canvas.scan_dragto(event.x, event.y, gain=self._zoom_ratio)

    def _reload(self):
        self._refresh_viewer()
        if not self._status_object.alive:
            self._main_window.quit()
            return
        self._main_window.after(50, self._reload)

    def _refresh_viewer(self):
        try:
            refreshed_photo = PhotoImage(file=self._file_name).subsample(self._zoom_ratio)
            self._canvas.itemconfig(self._image_on_canvas, image=refreshed_photo)
            self._img = refreshed_photo
            self._update_scroll_area()
        except:
            pass


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
        self._viewer_thread = threading.Thread(target=GraphViewer, args=(title + ".png", self._status))
        self.crawler = crawler  # intentionally public
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

    def _set_node(self, state, current_state, error_state):
        source_node = pydot.Node(state.__name__)
        source_node.set_style("filled")
        if state is error_state:
            color = "red"
            text_color = "black"
        elif state is current_state:
            color = "forestgreen"
            text_color = "white"
        else:
            color = "white"
            text_color = "black"
        source_node.set_fillcolor(color)
        source_node.set_fontcolor(text_color)
        source_node.set_shape("box")
        self._graph.add_node(source_node)

    def _set_edge(self, transition, current_transition, error_transition):
        if not transition.source_state:
            return
        edge = pydot.Edge(transition.source_state.__name__, transition.target_state.__name__)
        if transition is error_transition:
            color = "red"
            text_color = "red"
        elif transition is current_transition:
            color = "forestgreen"
            text_color = "forestgreen"
        else:
            color = "black"
            text_color = "black"
        edge.set_color(color)
        edge.set_fontcolor(text_color)
        edge.set_label(transition.__name__)
        self._graph.add_edge(edge)

    def _gen_graph(self, source_state, cur_state, cur_transition, error_state, error_transition):
        for target_state, transition in source_state.transition_map.iteritems():
            if transition in self._processed_transitions:
                continue
            self._processed_transitions.add(transition)
            self._set_node(target_state, cur_state, error_state)
            self._set_edge(transition, cur_transition, error_transition)
            self._gen_graph(target_state, cur_state, cur_transition, error_state, error_transition)

    def _save(self):
        self._processed_transitions = set()
        self._graph = pydot.Dot(self._title, graph_type='digraph')
        self._graph.set_splines("polyline")
        cr = self.crawler
        self._gen_graph(cr._initial_state, cr._current_state, cr._current_transition,
                        cr._error_state, cr._error_transition)
        self._graph.write_png(self._title + ".png")

    def __call__(self):
        self._save()

    def start(self):
        """ Launches the monitor in a separate thread """
        if not self._can_be_started:
            return
        if self._status.alive:
            return
        if not self.crawler:
            return
        self._status.alive = True
        self._viewer_thread.start()

    def stop(self):
        """ Stops the monitor """
        if not self._status.alive:
            return
        self._status.alive = False
        self._viewer_thread.join()
