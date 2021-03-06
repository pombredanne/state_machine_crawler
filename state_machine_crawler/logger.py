import sys
import traceback


class Color:
    RED = "\033[1;91m"
    GREEN = "\033[1;92m"
    BLUE = "\033[1;94m"
    NO_COLOR = "\033[0m"


class Symbol:
    PASS = u"\u2713"
    FAIL = u"\u2717"
    UNKNOWN = "?"


class StateLogger(object):

    def __init__(self, debug=False):
        self._debug = debug

    def make_debug(self):
        self._debug = True

    def _pr(self, msg):
        if self._debug:
            sys.stdout.write(msg)
            sys.stdout.flush()

    def _pass(self):
        self._pr("[+]")

    def _fail(self):
        self._pr("[-]")

    def _unknown(self):
        self._pr("[?]")

    def _c(self, flag):
        if flag is True:
            self._pass()
        elif flag is False:
            self._fail()
        else:
            self._unknown()

    def msg(self, current_state, next_state):
        self._pr("+ " + current_state.full_name + " -> " + next_state.full_name)
        self._pr("\n")

    def ok(self):
        self._c(True)
        self._pr("\n")

    def nok(self):
        self._c(False)
        self._pr("\n")

    def transition(self):
        self._pr("\tTransition   ")

    def verification(self):
        self._pr("\tVerification ")

    def show_traceback(self):
        if self._debug:
            self._pr("\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n")
            traceback.print_exc()
            self._pr("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<\n")

    def err(self, msg):
        self._pr(str(msg))
