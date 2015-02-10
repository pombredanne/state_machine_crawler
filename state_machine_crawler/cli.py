import argparse
import time

from .state_machine_crawler import TransitionError
from .webview import WebView


def cli(scm):

    def existing_state(name):
        states = dict(map(lambda state: (state.full_name, state), scm._state_graph.keys()))
        found = []
        for state_name, state in states.iteritems():
            if name in state_name:
                found.append(state)
        if not found:
            raise argparse.ArgumentTypeError("Target state does not exist")
        elif len(found) > 1:
            raise argparse.ArgumentTypeError("Too many states match the specified name")
        else:
            return found[0]

    parser = argparse.ArgumentParser(description='Manipulate the state machine')
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-t", "--target-state", help="State to which the system should be transitioned",
                       type=existing_state)
    group.add_argument("-a", "--all", action="store_true", help="Exercise all states")
    group.add_argument("-s", "--some", help="Exercise all states names of which match a regexp")
    parser.add_argument("-w", "--with-webview", action="store_true", help="Indicates if webview should be started")
    args = parser.parse_args()

    state_monitor = WebView(scm)

    def _stop():
        time.sleep(0.3)  # to make sure that the monitor reflects the final state of the system
        state_monitor.stop()

    try:
        if args.with_webview:
            state_monitor.start()
        if args.all:
            scm.verify_all_states()
        elif args.target_state:
            scm.move(args.target_state)
    except TransitionError, e:
        print e
    finally:
        _stop()
    _stop()
