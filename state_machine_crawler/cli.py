import argparse
import time
import logging

from .state_machine_crawler import TransitionError, LOG
from .webview import WebView


def cli(scm):
    """

    scm(:class:`StateMachineCrawler <state_machine_crawler.StateMachineCrawler>` instance)
        State machine to be given a command line interface

    Available command line arguments:

    *-t, --target-state*
        State to which the system should be transitioned
    *-a, --all*
        Exercise all states
    *-s, --some*
        Exercise all state names of which match a regexp
    *-w, --with-webview*
        Indicates if webview should be started
    *-c, --current-state*
        If it is known that the system is in specific state - it is possible to specify it and avoid extra transitions
    *-d, --debug*
        Outputs a detailed transition log

    NOTE: *-t*, *-a* and *-s* arguments are mutually exclusive

    Sample code:

    .. code:: python

        ...

        scm = StateMachineCrawler(InitialState)

        if __name__ == "__main__":
            cli(scm)

    """

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
    group.add_argument("-s", "--some", help="Exercise all state names of which match a regexp")
    parser.add_argument("-w", "--with-webview", action="store_true", help="Indicates if webview should be started")
    parser.add_argument("-c", "--current-state", type=existing_state,
                        help="If it is known that the system is in specific state - it is possible to specify it and"
                        " avoid extra transitions")
    parser.add_argument("-d", "--debug", action="store_true", help="print debug messages to stderr")
    args = parser.parse_args()

    if args.current_state:
        scm._current_state = args.current_state

    if args.debug:
        LOG.setLevel(logging.DEBUG)

    state_monitor = WebView(scm)

    def _stop():
        time.sleep(0.5)  # to make sure that the monitor reflects the final state of the system
        state_monitor.stop()

    try:
        if args.with_webview:
            state_monitor.start()
        if args.all:
            scm.verify_all_states()
        elif args.some:
            scm.verify_all_states(args.some)
        elif args.target_state:
            scm.move(args.target_state)
    except TransitionError, e:
        print e
    finally:
        _stop()
    _stop()
