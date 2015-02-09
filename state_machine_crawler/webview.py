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
    """

    cost (state_machine):
        :class:`StateMachineCrawler <state_machine_crawler.StateMachineCrawler>` instance

    Sample usage:

    >>> app = WebView(state_machine)
    >>> try:
    >>>     app.start()
    >>>     state_machine.verify_all_states()
    >>> except TransitionError, e:
    >>>     print e
    >>> except KeyboardInterrupt:
    >>>     pass
    >>> app.stop()

    Once the code is executed, a web service monitoring your state machine shall be started under a random available
    port in a separate thread. The url shall be printed to stdout to ease the access.

    An html page of the web service is a dynamic view of the state graph that represents the state machine.
    """

    HOST = 'localhost'

    def __init__(self, state_machine):
        self._state_machine = state_machine
        self._viewer_thread = threading.Thread(target=self._run_server)
        self._alive = True
        self._server = None

        url_map = [
            Rule("/", endpoint=partial(self._static, path="index.html")),
            Rule("/kill", endpoint=None),
            Rule("/graph.svg", endpoint=self._graph),
            Rule("/<string:path>", endpoint=self._static)
        ]

        self._url_map = Map(url_map)

    def _graph(self, request):
        dot = repr(self._state_machine)
        graph = pydot.graph_from_dot_data(dot)
        resp = Response(graph.create_svg())
        resp.mimetype = "image/svg+xml"
        return resp

    def _static(self, request, path):
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
