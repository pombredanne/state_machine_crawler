import unittest
import time
import sys

import mock

from state_machine_crawler import transition, StateMachineCrawler, DeclarationError, TransitionError, \
    State as BaseState, WebView, UnreachableStateError, NonExistentStateError, MultipleStatesError
from state_machine_crawler.state_machine_crawler import _create_state_map, _find_shortest_path, \
    _create_state_map_with_exclusions, _get_missing_nodes, _dfs, _equivalent, _create_transition_map
from state_machine_crawler.serializers.dot import Serializer
from state_machine_crawler.serializers.hierarchy import create_hierarchy

EXEC_TIME = 0


DOT_GRAPH = """digraph StateMachine {
    splines=polyline;
     concentrate=true;
     rankdir=LR;
    state_machine_crawler_state_machine_crawler_EntryPoint [style=filled label="+" shape=doublecircle fillcolor=forestgreen fontcolor=white];
    subgraph cluster_1 {
        label="tests";
        color=blue;
        fontcolor=blue;
        tests_StateThreeVariantOne [style=filled label="StateThreeVariantOne" shape=box fillcolor=white fontcolor=black];
        tests_StateFour [style=filled label="StateFour" shape=box fillcolor=white fontcolor=black];
        tests_StateTwo [style=filled label="StateTwo" shape=box fillcolor=blue fontcolor=white];
        tests_StateOne [style=filled label="StateOne" shape=box fillcolor=forestgreen fontcolor=white];
        tests_StateThreeVariantTwo [style=filled label="StateThreeVariantTwo" shape=box fillcolor=white fontcolor=black];
        tests_InitialState [style=filled label="InitialState" shape=box fillcolor=forestgreen fontcolor=white];
    }
    tests_StateThreeVariantOne -> tests_StateFour [color=black fontcolor=black label=" "];
    tests_StateTwo -> tests_StateThreeVariantTwo [color=black fontcolor=black label=" "];
    tests_StateTwo -> tests_StateThreeVariantOne [color=black fontcolor=black label="$2"];
    state_machine_crawler_state_machine_crawler_EntryPoint -> tests_InitialState [color=forestgreen fontcolor=forestgreen label=" "];
    tests_StateOne -> tests_StateTwo [color=forestgreen fontcolor=forestgreen label=" "];
    tests_StateOne -> tests_StateOne [color=black fontcolor=black label=" "];
    tests_StateThreeVariantTwo -> tests_StateFour [color=black fontcolor=black label=" "];
    tests_InitialState -> tests_StateOne [color=forestgreen fontcolor=forestgreen label=" "];
}"""


class State(BaseState):

    def verify(self):
        time.sleep(EXEC_TIME)
        self._system.visited(self.__class__.__name__)
        self._system.ok()


class InitialState(State):

    @transition(source_state=StateMachineCrawler.EntryPoint)
    def init(self):
        time.sleep(EXEC_TIME)
        self._system.enter()


class UnknownState(State):
    pass


class StateOne(State):

    @transition(source_state=InitialState)
    def from_initial_state(self):
        time.sleep(EXEC_TIME)
        self._system.unique()

    @transition(target_state="self")
    def reset(self):
        time.sleep(EXEC_TIME)
        self._system.reset()


class StateTwo(State):

    @transition(source_state=StateOne)
    def from_state_one(self):
        time.sleep(EXEC_TIME)
        self._system.unique()


class StateThreeVariantOne(State):

    @transition(source_state=StateTwo, cost=2)
    def move(self):
        time.sleep(EXEC_TIME)
        self._system.non_unique()


class StateThreeVariantTwo(State):

    @transition(source_state=StateTwo)
    def from_state_two(self):
        time.sleep(EXEC_TIME)
        self._system.unique()


class StateFour(State):

    @transition(source_state=StateThreeVariantOne)
    def from_v1(self):
        time.sleep(EXEC_TIME)
        self._system.non_unique()

    @transition(source_state=StateThreeVariantTwo)
    def from_v2(self):
        time.sleep(EXEC_TIME)
        self._system.non_unique()

    def verify(self):
        super(StateFour, self).verify()
        self._system.last_verify()


ALL_STATES = [
    InitialState,
    StateOne,
    StateTwo,
    StateThreeVariantOne,
    StateThreeVariantTwo,
    StateFour
]


class BaseFunctionsTest(unittest.TestCase):

    def test_create_state_map(self):

        rval = {}
        for key, value in _create_state_map(ALL_STATES).iteritems():
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

    def test_create_state_map_with_state_exclusions(self):
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

        self.assertEqual(_create_state_map_with_exclusions(graph, 0, exclusion_list), filtered_graph)
        self.assertEqual(_get_missing_nodes(graph, filtered_graph, 0), {1, 2, 4, 5, 9})

    def test_create_state_map_with_transition_exclusions(self):
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

        self.assertEqual(_create_state_map_with_exclusions(graph, 0, transition_exclusion_list=exclusion_list),
                         filtered_graph)
        self.assertEqual(_get_missing_nodes(graph, filtered_graph, 0), {1, 3, 4, 5, 9})

    def test_find_shortest_path(self):
        graph = _create_state_map(ALL_STATES)
        transitions = _create_transition_map(graph)

        def get_cost(states):
            cost = 0
            cursor = states[0]
            for state in states[1:]:
                cost += transitions[cursor, state].cost
                cursor = state
            return cost

        shortest_path = _find_shortest_path(graph, InitialState, StateFour, get_cost=get_cost)
        self.assertEqual(shortest_path, [InitialState, StateOne, StateTwo, StateThreeVariantTwo, StateFour])

    def test_unknown_state(self):
        graph = _create_state_map(ALL_STATES)
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
        cls.smc = StateMachineCrawler(cls.target, InitialState)
        for state in ALL_STATES:
            cls.smc.register_state(state)
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

    def test_move_with_string(self):
        self.smc.move("StateFour")
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

    def test_reset_the_state(self):
        self.smc.move(StateOne)
        self.assertEqual(self.target.reset.call_count, 0)
        self.smc.move(StateOne)
        self.assertEqual(self.target.reset.call_count, 1)

    def test_all(self):
        self.smc.verify_all_states(full=True)
        visited_states = map(lambda item: item[0][0], self.target.visited.call_args_list)
        self.assertEqual(set(visited_states),
                         set(['StateTwo', 'StateThreeVariantOne', 'StateFour', 'InitialState', 'StateOne',
                              'StateThreeVariantTwo']))

    def test_some(self):
        self.smc.verify_all_states(pattern=".*StateOne", full=True)
        visited_states = map(lambda item: item[0][0], self.target.visited.call_args_list)
        self.assertEqual(set(visited_states), set(['InitialState', 'StateOne']))

    def tearDown(self):
        self.target.reset_mock()
        self.smc.clear()


class NegativeTestCases(unittest.TestCase):

    def setUp(self):
        self.target = mock.Mock()
        self.smc = StateMachineCrawler(self.target, InitialState)
        for state in ALL_STATES:
            self.smc.register_state(state)

    def test_multiple_found_states(self):
        self.assertRaises(MultipleStatesError, self.smc.move, "State")

    def test_not_found_state(self):
        self.assertRaises(NonExistentStateError, self.smc.move, "FooBar")

    def test_unknown_state(self):
        self.assertRaises(NonExistentStateError, self.smc.move, UnknownState)

    def test_initial_state_verification_failure(self):
        self.target.enter.side_effect = Exception
        self.assertRaisesRegexp(TransitionError, "Move from state .+ to state .+ has failed",
                                self.smc.move, InitialState)
        self.assertRaisesRegexp(UnreachableStateError, "There is no way to achieve state %r" % StateOne,
                                self.smc.move, StateOne)

    def test_verification_error(self):
        self.target.ok.side_effect = Exception
        self.assertRaisesRegexp(TransitionError, "Move from state .+ to state .+ has failed",
                                self.smc.move, InitialState)

    def test_not_all_reachable(self):
        self.target.last_verify.side_effect = Exception
        self.assertRaisesRegexp(TransitionError, "Failed to visit the following states: %s" % StateFour,
                                self.smc.verify_all_states)

    def tearDown(self):
        self.target.reset_mock()


class TestStateMachineDeclaration(unittest.TestCase):

    def test_register_module(self):
        smc = StateMachineCrawler(mock.Mock(), InitialState)
        smc.register_module(sys.modules[self.__module__])
        self.assertEqual(len(smc._registered_states), 10)

    def test_register_not_a_state(self):

        class NotAState:
            pass

        smc = StateMachineCrawler(mock.Mock(), InitialState)
        self.assertRaisesRegexp(DeclarationError, "state must be a subclass of State",
                                smc.register_state, NotAState)

    def test_wrong_initial_state(self):

        class NotAState:
            pass

        self.assertRaisesRegexp(DeclarationError, ".+ is not a State subclass",
                                StateMachineCrawler, None, NotAState)

    def test_stateless_transition(self):

        def declare():

            class BadState(State):

                def verify(self):
                    return True

                @transition()
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

            @transition(target_state=PlainState)
            def move(self):
                pass


class TestStateMachineSerialization(BaseTestStateMachineTransitionCase):

    def test_repr(self):
        self.smc.move(StateTwo)
        value = repr(Serializer(self.smc))
        target_lines = DOT_GRAPH.replace("\n", "").replace("    ", "").replace("}", "};").replace("{", "{;").split(";")
        real_lines = value.replace("}", "};").replace("{", "{;").split(";")
        print value.replace(";", ";\n    ").replace("}", "}\n    ").replace("{", "{\n    ")
        self.assertEqual(sorted(real_lines), sorted(target_lines))


class TestTransitionEquivalence(unittest.TestCase):

    def test_subclasses(self):

        class Parent(State):
            pass

        class Super(State):

            @transition(target_state=Parent)
            def move(self):
                pass

        class ChildOne(Super):
            pass

        class ChildTwo(Super):
            pass

        self.assertFalse(_equivalent(ChildOne.move, ChildTwo.move))

    def test_missing_transitions(self):
        self.assertFalse(_equivalent(None, None))


class TestHierarchy(unittest.TestCase):

    def test_main(self):
        smc = StateMachineCrawler(None, InitialState)
        for state in ALL_STATES:
            smc.register_state(state)
        self.assertEqual(create_hierarchy(smc), {
            'state_machine_crawler': {
                'state_machine_crawler': {
                    'EntryPoint': smc.EntryPoint}},
            'tests': {
                'InitialState': InitialState,
                'StateFour': StateFour,
                'StateOne': StateOne,
                'StateThreeVariantOne': StateThreeVariantOne,
                'StateThreeVariantTwo': StateThreeVariantTwo,
                'StateTwo': StateTwo}})
