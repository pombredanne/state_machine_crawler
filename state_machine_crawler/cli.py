import argparse
import time
import os
import sys

from .state_machine_crawler import TransitionError
from .webview import WebView
from .serializers.svg import Serializer as SvgSerializer
from .serializers.text import Serializer as TextSerializer


FLAG_FILE = ".state_machine_crawler.flag"


def path_in_existing_directory(path):
    path = os.path.abspath(os.path.expanduser(path))
    dirname = os.path.dirname(path)
    if not os.path.exists(dirname):
        raise argparse.ArgumentTypeError("Directory %r does not exist" % dirname)
    if not os.path.isdir(dirname):
        raise argparse.ArgumentTypeError("%r is not a directory" % dirname)
    if not os.access(dirname, os.W_OK):
        raise argparse.ArgumentTypeError("Directory %r is not writable" % dirname)
    return path


def cli(scm):
    """

    scm(:class:`StateMachineCrawler <state_machine_crawler.StateMachineCrawler>` instance)
        State machine to be given a command line interface

    Available command line arguments:

    *-p, --transition_path*
        A path to a file with a chain of states to visit.
        The states must be delimited by '->'. E.g. 'A -> B -> C -> D -> Z'.
        It may be a standard input itself i.e. directed via a pipe.
    *-t, --target-state*
        State to which the system should be transitioned
    *-a, --all*
        Exercise all states
    *-s, --some*
        Exercise all state names of which match a regexp
    *-f, --full*
        Exercise not only all states but also all transitions
    *-w, --with-webview*
        Indicates if webview should be started
    *-c, --current-state*
        If it is known that the system is in specific state - it is possible to specify it and avoid extra transitions
    *-d, --debug*
        Outputs a detailed transition log
    *--without-flag*
        Set it to avoid storing the current state of the device in a file
    *--text*
        In the end of transition operations stores state machine's info in a text file @ desired location
    *--svg*
        In the end of transition operations stores state machine's info as an svg image @ desired location

    NOTE: *-t*, *-a*, *-f*, *-s* and *-p* arguments are mutually exclusive

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
    group.add_argument("-p", "--transition-path", type=argparse.FileType('r'), default=sys.stdin,
                       help="A path to a file with a chain of states to visit. "
                            "The states must be delimited by '->'. E.g. 'A -> B -> C -> D -> Z'. "
                            "It may be a standard input itself i.e. directed via a pipe.")
    group.add_argument("-t", "--target-state", help="State to which the system should be transitioned",
                       type=existing_state)
    group.add_argument("-a", "--all", action="store_true", help="Exercise all states")
    group.add_argument("-s", "--some", help="Exercise all state names of which match a regexp")
    group.add_argument("-f", "--full", action="store_true",
                       help="Exercise not only all states but also all transitions")
    parser.add_argument("-w", "--with-webview", action="store_true", help="Indicates if webview should be started")
    parser.add_argument("-c", "--current-state", type=existing_state,
                        help="If it is known that the system is in specific state - it is possible to specify it and"
                        " avoid extra transitions")
    parser.add_argument("-d", "--debug", action="store_true", help="print debug messages to stderr")
    parser.add_argument("--text", type=path_in_existing_directory,
                        help="In the end of transition operations stores state machine's info in a text file "
                             "@ desired location")
    parser.add_argument("--without-flag", action="store_true",
                        help="Stores current state of the device to avoid usage of '-c' argument."
                             " '-c' overrides the flag.")
    parser.add_argument("--svg", type=path_in_existing_directory,
                        help="In the end of transition operations stores state machine's info as an svg image "
                             "@ desired location")
    args = parser.parse_args()

    if not args.without_flag:
        if os.path.exists(FLAG_FILE):
            with open(FLAG_FILE) as fil:
                scm._current_state = existing_state(fil.read())

    if args.current_state:
        scm._current_state = args.current_state

    if args.debug:
        scm.log.make_debug()

    state_monitor = WebView(scm)

    def _stop():
        time.sleep(0.5)  # to make sure that the monitor reflects the final state of the system
        state_monitor.stop()

    ok = True

    try:
        if args.with_webview:
            state_monitor.start()
            time.sleep(0.5)  # to make sure that the web app is started before the state machine
        if args.all:
            scm.verify_all_states()
        elif args.full:
            scm.verify_all_states(full=True)
        elif args.some:
            scm.verify_all_states(args.some)
        elif args.target_state:
            scm.move(args.target_state)
        elif args.transition_path:
            states = [existing_state(state.strip()) for state in args.transition_path.read().split("->")]
            scm.move(states[0])
            for state in states[1:]:
                scm._do_step(state)
        else:
            parser.print_help()
    except TransitionError, e:
        ok = False
        print(e)
    finally:
        _stop()
    _stop()

    if not args.without_flag:
        with open(FLAG_FILE, "w") as fil:
            fil.write(scm._current_state.full_name)

    if args.text:
        with open(args.text, "w") as fil:
            fil.write(repr(TextSerializer(scm)))

    if args.svg:
        with open(args.svg, "w") as fil:
            fil.write(repr(SvgSerializer(scm)))

    if not ok:
        return sys.exit(1)
