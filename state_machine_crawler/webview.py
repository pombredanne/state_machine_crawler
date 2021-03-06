import os
import mimetypes
import urllib
from functools import partial
import threading
import urllib2
import socket
import atexit
from wsgiref.simple_server import make_server, WSGIRequestHandler, WSGIServer

from werkzeug.wrappers import Response, Request
from werkzeug.routing import Map, Rule
from werkzeug.wsgi import wrap_file

from .serializers import svg, text, dot


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _silent(call, *args):
    try:
        call(*args)
    except Exception:
        pass


class SilentHandler(WSGIRequestHandler):

    def log_message(self, *args, **kwargs):
        pass


class WSGIServerWithReusableSocket(WSGIServer):
    allow_reuse_address = True


class WebView(object):
    """

    state_machine(:class:`StateMachineCrawler <state_machine_crawler.StateMachineCrawler>` instance)
        State machine to be monitored

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

    Once the code is executed, a web service monitoring your state machine shall be started under
    `http://localhost:8666 <http://localhost:8666>`_. The url shall be printed to stdout to ease the access.

    An html page of the web service is a dynamic view of the graph that represents the state machine.
    """

    HOST = 'localhost'

    SERIALIZER_MAP = {
        "svg": svg,
        "txt": text,
        "dot": dot
    }

    def __init__(self, state_machine):
        self._state_machine = state_machine
        self._viewer_thread = threading.Thread(target=self._run_server)
        self._alive = False
        self._server = None

        url_map = [
            Rule("/", endpoint=partial(self._static, path="index.html")),
            Rule("/kill", endpoint=None),
            Rule("/graph.<string:serializer_type>", endpoint=self._graph),
            Rule("/<string:path>", endpoint=self._static)
        ]

        self._url_map = Map(url_map)

    def _graph(self, request, serializer_type):

        serializer_class = self.SERIALIZER_MAP.get(serializer_type, text).Serializer

        resp = Response(repr(serializer_class(self._state_machine)))
        resp.mimetype = serializer_class.mimetype
        return resp

    def _static(self, request, path):
        root = os.path.join(os.path.dirname(__file__), "webview")
        file_name = path.lstrip("/").replace("/", os.path.sep)

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
        self._server = httpd = make_server(self.HOST, 8666, self, server_class=WSGIServerWithReusableSocket,
                                           handler_class=SilentHandler)
        print("Started the server at http://%s:%d" % (self.HOST, httpd.server_port))

        def close_socket():
            _silent(httpd.socket.shutdown, socket.SHUT_RDWR)
            _silent(httpd.socket.close)

        atexit.register(close_socket)

        while self._alive:
            httpd.handle_request()

    def start(self):
        if self._alive:
            return
        self._alive = True
        self._viewer_thread.start()

    def stop(self):
        if not self._alive:
            return
        self._alive = False
        try:
            urllib2.urlopen("http://%s:%d/kill" % (self.HOST, self._server.server_port), timeout=3)
        except socket.error:
            pass
        self._viewer_thread.join()
