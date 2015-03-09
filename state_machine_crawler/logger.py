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

    def _pr(self):
        if self._debug:
            sys.stdout.write(u"\r" + self._msg)
            sys.stdout.flush()

    def _c(self, flag):
        if flag is True:
            self._msg += "[" + Color.GREEN + Symbol.PASS + Color.NO_COLOR + "]"
        elif flag is False:
            self._msg += "[" + Color.RED + Symbol.FAIL + Color.NO_COLOR + "]"
        else:
            self._msg += "[" + Color.BLUE + Symbol.UNKNOWN + Color.NO_COLOR + "]"

    def msg(self, current_state, next_state, transition_ok=None, verification_ok=None):
        self._msg = ""
        self._c(transition_ok)
        self._c(verification_ok)
        self._msg += "[{:65s}]".format(current_state.full_name + " -> " + next_state.full_name)
        self._pr()

    def fin(self):
        if self._debug:
            sys.stdout.write("\n")

    def err(self, msg=None):
        if self._debug:
            if msg:
                print(str(msg))
            else:
                traceback.print_exc()
