import json
import sys
import os

from .cli import cli


STATE_MACHINE_CONFIG = "state_machine_crawler.json"


class StateMachineDiscoveryError(Exception):
    pass


def find_config_file():
    for root, _, files in os.walk(os.path.abspath(os.path.curdir)):
        if STATE_MACHINE_CONFIG in files:
            return os.path.join(root, STATE_MACHINE_CONFIG)


def _import(name):
    parts = name.split(".")

    module_name_parts = parts[:-1]
    instance_name = parts[-1]

    m = __import__(".".join(module_name_parts))

    try:
        for n in module_name_parts[1:]:
            m = getattr(m, n)

        return getattr(m, instance_name)
    except AttributeError:
        raise ImportError("Could not import %r" % name)


def entry_point():
    """
    Entry point **state-machine-crawler** to manipulate the state machine via a command line.

    Discovers state machine's instance based on data from 'state_machine_crawler.json' file.

    JSON config file must have an 'instance' field that has to represent a Python module name of a
    :class:`StateMachineCrawler <state_machine_crawler.StateMachineCrawler>` instance.

    It also may contain a 'path' field that would be either a relative (with respect to parent directory of a the
    config file) or an absolute file path leading to the directory that contains Python code for the particular state
    machine.

    An example of a valid JSON config file:

    .. code:: json

        {
            "path": "functional_tests",
            "instance" "functional_tests.instance.state_machine"
        }

    Sample command line usage:

    .. code:: bash

        state-machine-crawler -d -w -f

    Note, it is impossible to use any command line option if the config file is not specified correctly.
    """

    config_file_path = find_config_file()

    if not config_file_path:
        raise StateMachineDiscoveryError("Could not find %r in a directory tree" % STATE_MACHINE_CONFIG)

    with open(config_file_path) as fil:
        try:
            config = json.load(fil)
        except ValueError:
            raise StateMachineDiscoveryError("Could not parse %r" % config_file_path)

    state_machine_path = config.get("path")
    state_machine_instance = config.get("instance")

    if state_machine_path:
        project_dir = os.path.dirname(config_file_path)
        sys.path.append(project_dir)
        sys.path.append(os.path.join(project_dir, state_machine_path))

    if not state_machine_instance:
        raise StateMachineDiscoveryError("StateMachine's 'instance' is not defined")

    try:
        scm = _import(state_machine_instance)
    except ImportError:
        raise StateMachineDiscoveryError("Failed to import %r" % state_machine_instance)

    cli(scm)


if __name__ == "__main__":
    entry_point()
