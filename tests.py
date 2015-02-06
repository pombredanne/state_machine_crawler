import unittest
import time

import mock

from state_machine_crawler import Transition, StateMachineCrawler, DeclarationError, TransitionError, \
    State as BaseState, WebView
from state_machine_crawler.state_machine_crawler import _create_transition_map, _find_shortest_path, LOG, \
    _create_transition_map_with_exclusions, _get_missing_nodes, _dfs

LOG.handlers = []

EXEC_TIME = 0


DOT_GRAPH = """digraph StateMachine {splines=polyline; concentrate=true; rankdir=LR;
    EntryPoint [style=filled label="+" shape=doublecircle fillcolor=white fontcolor=black];

    subgraph cluster_1 {
        label="tests";
        color=blue;
        fontcolor=blue;
        InitialState [style=filled label="InitialState" shape=box fillcolor=yellow fontcolor=black];
        StateOne [style=filled label="StateOne" shape=box fillcolor=yellow fontcolor=black];
        StateTwo [style=filled label="StateTwo" shape=box fillcolor=forestgreen fontcolor=white];
        StateFour [style=filled label="StateFour" shape=box fillcolor=white fontcolor=black];
        StateThreeVariantOne [style=filled label="StateThreeVariantOne" shape=box fillcolor=white fontcolor=black];
        StateThreeVariantTwo [style=filled label="StateThreeVariantTwo" shape=box fillcolor=white fontcolor=black];
    }

    InitialState -> StateOne [color=yellow fontcolor=black label="$1"];
    EntryPoint -> InitialState [color=black fontcolor=black label="$1"];
    StateOne -> StateTwo [color=forestgreen fontcolor=forestgreen label="$1"];
    StateOne -> StateOne [color=black fontcolor=black label="$1"];
    StateTwo -> StateThreeVariantOne [color=black fontcolor=black label="$2"];
    StateTwo -> StateThreeVariantTwo [color=black fontcolor=black label="$1"];
    StateThreeVariantOne -> StateFour [color=black fontcolor=black label="$1"];
    StateThreeVariantTwo -> StateFour [color=black fontcolor=black label="$1"];

}"""


class State(BaseState):

    def verify(self):
        time.sleep(EXEC_TIME)
        self._system.visited(self.__class__.__name__)
        return self._system.ok()


class InitialState(State):
    pass


class InitialTransition(Transition):
    target_state = InitialState

    def move(self):
        time.sleep(EXEC_TIME)
        self._system.enter()


class UniqueTransition(Transition):

    def move(self):
        time.sleep(EXEC_TIME)
        self._system.unique()


class NonUniqueTransition(Transition):

    def move(self):
        time.sleep(EXEC_TIME)
        self._system.non_unique()


class UnknownState(State):
    pass


class StateOne(State):
    from_initial_state = UniqueTransition.link(source_state=InitialState)

    class reset_transition(Transition):
        target_state = "self"

        def move(self):
            time.sleep(EXEC_TIME)
            self._system.reset()


class StateTwo(State):
    from_state_one = UniqueTransition.link(source_state=StateOne)


class StateThreeVariantOne(State):

    class from_state_two(NonUniqueTransition):
        cost = 2
        source_state = StateTwo


class StateThreeVariantTwo(State):
    from_state_two = UniqueTransition.link(source_state=StateTwo)


class StateFour(State):
    from_v1 = NonUniqueTransition.link(source_state=StateThreeVariantOne)
    from_v2 = NonUniqueTransition.link(source_state=StateThreeVariantTwo)

    def verify(self):
        if not super(StateFour, self).verify():
            return False
        return bool(self._system.last_verify())


class BaseFunctionsTest(unittest.TestCase):

    def test_create_transition_map(self):

        rval = {}
        for key, value in _create_transition_map(InitialState).iteritems():
            if key.__name__ == "EntryPoint":
                continue
            rval[key] = value

        self.assertEqual({
            InitialState: {StateOne},
            StateOne: {StateTwo, StateOne},
            StateTwo: {StateThreeVariantOne, StateThreeVariantTwo},
            StateThreeVariantOne: {StateFour},
            StateThreeVariantTwo: {StateFour},
            StateFour: set()
        }, rval)

    def test_create_transition_map_with_state_exclusions(self):
        graph = {
            0: {1, 2, 3},
            1: {4, 5},
            2: {6, 9},
            3: {6},
            6: {7, 8}
        }

        exclusion_list = [1, 2]

        filtered_graph = {
            0: {3},
            3: {6},
            6: {7, 8}
        }

        self.assertEqual(_create_transition_map_with_exclusions(graph, 0, exclusion_list), filtered_graph)
        self.assertEqual(_get_missing_nodes(graph, filtered_graph, 0), {1, 2, 4, 5, 9})

    def test_create_transition_map_with_transition_exclusions(self):
        graph = {
            0: {1, 2, 3},
            1: {4, 5},
            2: {6, 9},
            3: {6},
            6: {7, 8}
        }

        exclusion_list = [(0, 1), (0, 3), (2, 9)]

        filtered_graph = {
            0: {2},
            2: {6},
            6: {7, 8}
        }

        self.assertEqual(_create_transition_map_with_exclusions(graph, 0, transition_exclusion_list=exclusion_list),
                         filtered_graph)
        self.assertEqual(_get_missing_nodes(graph, filtered_graph, 0), {1, 3, 4, 5, 9})

    def test_find_shortest_path(self):
        graph = _create_transition_map(InitialState)

        def get_cost(states):
            cost = 0
            cursor = states[0]
            for state in states[1:]:
                cost += cursor.transition_map[state].cost
                cursor = state
            return cost

        shortest_path = _find_shortest_path(graph, InitialState, StateFour, get_cost=get_cost)
        self.assertEqual(shortest_path, [InitialState, StateOne, StateTwo, StateThreeVariantTwo, StateFour])

    def test_unknown_state(self):
        graph = _create_transition_map(InitialState)
        shortest_path = _find_shortest_path(graph, UnknownState, StateFour)
        self.assertIs(shortest_path, None)

    def test_dfs(self):
        graph = {"A": ["B", "C", "A"],
                 "B": ["D", "E", "A"],
                 "D": ["B", "A"],
                 "E": ["B", "A"],
                 "C": ["F", "G", "A"],
                 "F": ["C", "A"],
                 "G": ["C", "A"]}
        self.assertEqual(_dfs(graph, "A"), ['A', 'C', 'G', 'F', 'B', 'E', 'D'])


class BaseTestStateMachineTransitionCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.target = mock.Mock()
        cls.smc = StateMachineCrawler(cls.target, InitialTransition)
        if EXEC_TIME:
            cls.viewer = WebView(cls.smc)
            cls.viewer.start()

    @classmethod
    def tearDownClass(cls):
        if EXEC_TIME:
            cls.viewer.stop()


class PositiveTestStateMachineTransitionTest(BaseTestStateMachineTransitionCase):

    def setUp(self):
        self.smc.move(InitialState)

    def test_move(self):
        self.smc.move(StateFour)
        self.assertEqual(self.target.enter.call_count, 1)
        self.assertEqual(self.target.unique.call_count, 3)
        self.assertEqual(self.target.non_unique.call_count, 1)

    def test_sequential_moves(self):
        self.assertIs(self.smc.state, InitialState)
        self.smc.move(StateOne)
        self.assertIs(self.smc.state, StateOne)
        self.smc.move(StateTwo)
        self.assertIs(self.smc.state, StateTwo)
        self.smc.move(StateFour)
        self.assertIs(self.smc.state, StateFour)

    def test_move_through_initial_state(self):
        self.smc.move(StateFour)
        self.smc.move(StateTwo)
        self.assertIs(self.smc.state, StateTwo)

    def test_unknown_state(self):
        self.assertRaises(TransitionError, self.smc.move, UnknownState)

    def test_reset_the_state(self):
        self.smc.move(StateOne)
        self.assertEqual(self.target.reset.call_count, 0)
        self.smc.move(StateOne)
        self.assertEqual(self.target.reset.call_count, 1)

    def test_all(self):
        self.smc.verify_all_states()
        visited_states = map(lambda item: item[0][0], self.target.visited.call_args_list)
        self.assertEqual(set(visited_states),
                         set(['StateTwo', 'StateThreeVariantOne', 'StateFour', 'InitialState', 'StateOne',
                              'StateThreeVariantTwo']))

    def test_some(self):
        self.smc.verify_all_states(pattern=".*StateOne")
        visited_states = map(lambda item: item[0][0], self.target.visited.call_args_list)
        self.assertEqual(set(visited_states), set(['InitialState', 'StateOne']))

    def tearDown(self):
        self.target.reset_mock()
        self.smc.clear()


class NegativeTestCases(unittest.TestCase):

    def setUp(self):
        self.target = mock.Mock()
        self.smc = StateMachineCrawler(self.target, InitialTransition)

    def test_state_verification_failure(self):
        self.smc.move(InitialState)
        self.target.ok.return_value = False
        self.assertRaisesRegexp(TransitionError, "Move from state .+ to state .+ has failed", self.smc.move, StateOne)

    def test_initial_state_verification_failure(self):
        self.target.ok.return_value = False
        self.assertRaisesRegexp(TransitionError, "Move from state .+ to state .+ has failed",
                                self.smc.move, InitialState)

    def test_initial_move_error(self):
        self.target.enter.side_effect = Exception
        self.assertRaisesRegexp(TransitionError, "Move from state .+ to state .+ has failed",
                                self.smc.move, InitialState)
        self.assertRaisesRegexp(TransitionError, "Move from state .+ to state .+ has failed",
                                self.smc.move, StateOne)

    def test_verification_error(self):
        self.target.ok.side_effect = Exception
        self.assertRaisesRegexp(TransitionError, "Move from state .+ to state .+ has failed",
                                self.smc.move, InitialState)

    def test_not_all_reachable(self):
        self.target.last_verify.return_value = False
        self.assertRaisesRegexp(TransitionError, "Failed to visit the following states: %s" % StateFour,
                                self.smc.verify_all_states)

    def tearDown(self):
        self.target.reset_mock()


class TestStateMachineDeclaration(unittest.TestCase):

    def test_wrong_initial_state_transition(self):

        class NotATransition:
            pass

        self.assertRaisesRegexp(DeclarationError, "initial_transition must be a Transition subclass",
                                StateMachineCrawler, None, NotATransition)

    def test_stateless_transition(self):

        def declare():

            class BadState(State):

                def verify(self):
                    return True

                class StatelessTransition(Transition):

                    def move(self):
                        pass

        self.assertRaisesRegexp(DeclarationError, "No target nor source state is defined for .+", declare)

    def test_normal_declaration(self):

        class PlainState(BaseState):

            def verify(self):
                return True

        class NormalState(BaseState):

            def verify(self):
                return True

            class NormalTransition(Transition):
                target_state = PlainState

                def move(self):
                    pass

    def test_initial_transition_without_target_state(self):

        class PlainState(BaseState):

            def verify(self):
                return True

        class NormalTransition(Transition):
            source_state = PlainState

            def move(self):
                pass

        self.assertRaisesRegexp(DeclarationError, "initial transition has no target state",
                                StateMachineCrawler, None, NormalTransition)


class TestStateMachineSerialization(BaseTestStateMachineTransitionCase):

    def test_repr(self):
        self.smc.move(StateTwo)
        value = repr(self.smc)
        target_lines = DOT_GRAPH.replace("\n", "").replace("    ", "").replace("}", "};").replace("{", "{;").split(";")
        real_lines = value.replace("}", "};").replace("{", "{;").split(";")
        print value.replace(";", ";\n    ").replace("}", "}\n    ").replace("{", "{\n    ")
        self.assertEqual(sorted(real_lines), sorted(target_lines))
