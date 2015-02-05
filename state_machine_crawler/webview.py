import os
import mimetypes
import urllib
from functools import partial
import threading
import urllib2
from wsgiref.simple_server import make_server, WSGIRequestHandler

from werkzeug.wrappers import Response, Request
from werkzeug.routing import Map, Rule
from werkzeug.wsgi import wrap_file

import pydot


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class SilentHandler(WSGIRequestHandler):

    def log_message(self, *args, **kwargs):
        pass


class WebView(object):

    HOST = 'localhost'

    def __init__(self, state_machine):
        self._state_machine = state_machine
        self._viewer_thread = threading.Thread(target=self._run_server)
        self._alive = True
        self._server = None

        url_map = [
            Rule("/", endpoint=partial(self.static, path="index.html")),
            Rule("/kill", endpoint=None),
            Rule("/graph.svg", endpoint=self.graph),
            Rule("/<string:path>", endpoint=self.static)
        ]

        self._url_map = Map(url_map)

    def graph(self, request):
        dot = repr(self._state_machine)
        graph = pydot.graph_from_dot_data(dot)
        resp = Response(graph.create_svg())
        resp.mimetype = "image/svg+xml"
        return resp

    def static(self, request, path):
        local_path = os.path.join(PROJECT_DIR, "webview")
        file_name = path.lstrip("/").replace("/", os.path.sep)

        if os.path.exists(local_path):
            root = local_path
        else:
            root = "/usr/share/state_machine_crawler"

        abs_path = os.path.join(root, file_name)
        resp = Response()

        if not (os.path.exists(abs_path) and os.path.isfile(abs_path)):
            resp.status_code = 404
            return resp

        fil = open(abs_path)
        resp.direct_passthrough = True
        resp.response = wrap_file(request.environ, fil)

        url = urllib.pathname2url(abs_path)
        resp.mimetype = mimetypes.guess_type(url)[0]

        return resp

    def __call__(self, environ, start_response):
        urls = self._url_map.bind_to_environ(environ)
        endpoint, params = urls.match()
        if endpoint is None:
            resp = Response("Killed")
        else:
            resp = endpoint(Request(environ), **params)
        return resp(environ, start_response)

    def _run_server(self):
        self._server = httpd = make_server(self.HOST, 0, self, handler_class=SilentHandler)
        print("Started the server at http://%s:%d" % (self.HOST, httpd.server_port))
        while self._alive:
            httpd.handle_request()

    def start(self):
        self._alive = True
        self._viewer_thread.start()

    def stop(self):
        self._alive = False
        urllib2.urlopen("http://%s:%d/kill" % (self.HOST, self._server.server_port))
        self._viewer_thread.join()


if __name__ == "__main__":

    SAMPLE_GRAPH = """digraph StateMachine {
        splines=polyline;
        StateTwo [style=filled label="StateTwo" shape=box fillcolor=forestgreen fontcolor=white];
        EntryPoint [style=filled label="+" shape=doublecircle fillcolor=white fontcolor=black];
        StateThreeVariantOne [style=filled label="StateThreeVariantOne" shape=box fillcolor=white fontcolor=black];
        StateThreeVariantTwo [style=filled label="StateThreeVariantTwo" shape=box fillcolor=white fontcolor=black];
        StateFour [style=filled label="StateFour" shape=box fillcolor=white fontcolor=black];
        StateOne [style=filled label="StateOne" shape=box fillcolor=white fontcolor=black];
        InitialState [style=filled label="InitialState" shape=box fillcolor=white fontcolor=black];
        StateTwo -> StateThreeVariantTwo [color=black];
        StateTwo -> StateThreeVariantOne [color=black];
        EntryPoint -> InitialState [color=black];
        StateThreeVariantOne -> StateFour [color=black];
        StateThreeVariantTwo -> StateFour [color=black];
        StateOne -> StateTwo [color=forestgreen];
        StateOne -> StateOne [color=black];
        InitialState -> StateOne [color=black];
    }"""

    class FakeStateMachine(object):

        def __repr__(self):
            return SAMPLE_GRAPH

    app = WebView(FakeStateMachine())
    try:
        app.start()
        while True:
            pass
    except KeyboardInterrupt:
        app.stop()
