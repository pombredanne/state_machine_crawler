import unittest

import mock

from state_machine_crawler import transition, StateMachineCrawler, DeclarationError, TransitionError, \
    State as BaseState, WebView, UnreachableStateError, NonExistentStateError, MultipleStatesError, StateCollection
from state_machine_crawler.state_machine_crawler import _create_state_map, _find_shortest_path, \
    _create_state_map_with_exclusions, _get_missing_nodes, _dfs, _equivalent, _create_transition_map
from state_machine_crawler.serializers.dot import Serializer
from state_machine_crawler.serializers.hierarchy import create_hierarchy

from .cases import ALL_STATES, InitialState, StateOne, StateTwo, StateThreeVariantOne, StateThreeVariantTwo, \
    StateFour, EXEC_TIME, UnknownState, State
from .tpl_cases import TplStateOne, TplStateTwo
from . import non_tpl_cases


# dot -Tpng test.dot -o test.png
DOT_GRAPH = """digraph StateMachine {
    splines=polyline;
     concentrate=true;
     rankdir=LR;
    state_machine_crawler_state_machine_crawler_EntryPoint [style=filled label="+" shape=doublecircle fillcolor=forestgreen fontcolor=white];
    subgraph cluster_2 {
    label="tests";
    color=blue;
    fontcolor=blue;
    subgraph cluster_3 {
    label="cases";
    color=blue;
    fontcolor=blue;
    tests_cases_StateTwo [style=filled label="StateTwo" shape=box fillcolor=blue fontcolor=white];
    tests_cases_StateThreeVariantOne [style=filled label="StateThreeVariantOne" shape=box fillcolor=white fontcolor=black];
    tests_cases_StateFour [style=filled label="StateFour" shape=box fillcolor=white fontcolor=black];
    tests_cases_InitialState [style=filled label="InitialState" shape=box fillcolor=forestgreen fontcolor=white];
    tests_cases_StateOne [style=filled label="StateOne" shape=box fillcolor=forestgreen fontcolor=white];
    tests_cases_StateThreeVariantTwo [style=filled label="StateThreeVariantTwo" shape=box fillcolor=white fontcolor=black];
    }
    }
    tests_cases_StateThreeVariantTwo -> tests_cases_StateFour [color=black fontcolor=black label=" "];
    tests_cases_StateOne -> tests_cases_StateOne [color=black fontcolor=black label=" "];
    tests_cases_StateOne -> tests_cases_StateTwo [color=forestgreen fontcolor=forestgreen label=" "];
    tests_cases_InitialState -> tests_cases_StateOne [color=forestgreen fontcolor=forestgreen label=" "];
    state_machine_crawler_state_machine_crawler_EntryPoint -> tests_cases_InitialState [color=forestgreen fontcolor=forestgreen label=" "];
    tests_cases_StateThreeVariantOne -> tests_cases_StateFour [color=black fontcolor=black label=" "];
    tests_cases_StateTwo -> tests_cases_StateThreeVariantOne [color=black fontcolor=black label="$2"];
    tests_cases_StateTwo -> tests_cases_StateThreeVariantTwo [color=black fontcolor=black label=" "];
}"""


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

    def test_base_state_registration(self):
        self.smc.register_state(BaseState)
        self.assertFalse(BaseState in self.smc._registered_states)

    def tearDown(self):
        self.target.reset_mock()


class TestStateMachineDeclaration(unittest.TestCase):

    def test_register_module(self):
        smc = StateMachineCrawler(mock.Mock(), InitialState)
        smc.register_module(non_tpl_cases)

        states = sorted([src.full_name for src in smc._state_graph])

        self.assertEqual(states, [
            'state_machine_crawler.state_machine_crawler.EntryPoint',
            'tests.cases.InitialState',
            'tests.cases.StateOne',
            'tests.cases.StateTwo',
            'tests.non_tpl_cases.TplStateOne',
            'tests.non_tpl_cases.TplStateTwo'
        ])

    def test_register_not_a_state(self):

        class NotAState:
            pass

        smc = StateMachineCrawler(mock.Mock(), InitialState)
        self.assertRaisesRegexp(DeclarationError, "state .* must be a subclass of State",
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

    def test_dict(self):
        smc = StateMachineCrawler(None, InitialState)
        for state in ALL_STATES:
            smc.register_state(state)
        self.assertEqual(create_hierarchy(smc), {
            'tests': {
                'cases': {
                    'InitialState': InitialState,
                    'StateFour': StateFour,
                    'StateOne': StateOne,
                    'StateThreeVariantOne': StateThreeVariantOne,
                    'StateThreeVariantTwo': StateThreeVariantTwo,
                    'StateTwo': StateTwo}}})

    def test_register_module_custom_name(self):
        smc = StateMachineCrawler(None, InitialState)
        smc.register_collection(StateCollection.from_module(non_tpl_cases, "FooBar"))
        result = create_hierarchy(smc)
        from pprint import pprint
        pprint(result)
        self.assertEqual(result, {
            'tests': {
                'cases': {
                    'StateOne': StateOne,
                    'StateTwo': StateTwo,
                    'InitialState': InitialState}},
            'FooBar': {
                'TplStateOne': mock.ANY,
                'TplStateTwo': mock.ANY}})

    def _assert_subclass(self, actual, expectation):
        self.assertFalse(actual is expectation)
        self.assertTrue(issubclass(actual, expectation))

    def _create_smc(self):
        sub_collection = StateCollection("sub_collection", {
            "unknown_target": StateOne,
            "another_unknown_target": StateTwo
        })
        sub_collection.register_state(TplStateOne)
        sub_collection.register_state(TplStateTwo)

        another_sub_collection = StateCollection("another_sub_collection", {
            "unknown_target": StateTwo,
            "another_unknown_target": StateOne
        })
        another_sub_collection.register_state(TplStateOne)
        another_sub_collection.register_state(TplStateTwo)

        collection = StateCollection("collection")
        collection.register_collection(sub_collection)
        collection.register_collection(another_sub_collection)

        smc = StateMachineCrawler(None, InitialState)
        smc.register_collection(collection)

        return smc

    def test_collection_hierarchy(self):
        result = create_hierarchy(self._create_smc())

        from pprint import pprint
        pprint(result)

        self.assertEqual(result, {
            'tests': {
                'cases': {
                    'StateOne': StateOne,
                    'StateTwo': StateTwo,
                    'InitialState': InitialState}},
            'collection': {
                'sub_collection': {
                    'TplStateOne': mock.ANY,
                    'TplStateTwo': mock.ANY
                },
                'another_sub_collection': {
                    'TplStateOne': mock.ANY,
                    'TplStateTwo': mock.ANY
                }}})
        self._assert_subclass(result["collection"]["sub_collection"]["TplStateOne"], TplStateOne)
        self._assert_subclass(result["collection"]["sub_collection"]["TplStateTwo"], TplStateTwo)
        self._assert_subclass(result["collection"]["another_sub_collection"]["TplStateOne"], TplStateOne)
        self._assert_subclass(result["collection"]["another_sub_collection"]["TplStateTwo"], TplStateTwo)

    def test_state_machine_internals(self):
        smc = self._create_smc()

        transitions = []
        for (source, target), trans in smc._transition_map.iteritems():
            if not isinstance(source, basestring):
                source = source.full_name
            if not isinstance(target, basestring):
                target = target.full_name
            transitions.append(source + " -(" + getattr(trans, "original", trans).__name__ + ")> " + target)

        result = sorted(transitions)

        from pprint import pprint
        pprint(result)

        self.assertEqual(result, [
            'collection.another_sub_collection.TplStateOne -(from_one)> collection.another_sub_collection.TplStateTwo',
            'collection.another_sub_collection.TplStateOne -(tempo)> state_machine_crawler.state_machine_crawler.EntryPoint',
            'collection.another_sub_collection.TplStateOne -(to_unknown_target)> tests.cases.StateTwo',
            'collection.another_sub_collection.TplStateTwo -(tempo)> state_machine_crawler.state_machine_crawler.EntryPoint',
            'collection.another_sub_collection.TplStateTwo -(to_another_unknown_target)> tests.cases.StateOne',
            'collection.sub_collection.TplStateOne -(from_one)> collection.sub_collection.TplStateTwo',
            'collection.sub_collection.TplStateOne -(tempo)> state_machine_crawler.state_machine_crawler.EntryPoint',
            'collection.sub_collection.TplStateOne -(to_unknown_target)> tests.cases.StateOne',
            'collection.sub_collection.TplStateTwo -(tempo)> state_machine_crawler.state_machine_crawler.EntryPoint',
            'collection.sub_collection.TplStateTwo -(to_another_unknown_target)> tests.cases.StateTwo',
            'state_machine_crawler.state_machine_crawler.EntryPoint -(init)> tests.cases.InitialState',
            'tests.cases.InitialState -(from_initial_state)> tests.cases.StateOne',
            'tests.cases.InitialState -(from_root)> collection.another_sub_collection.TplStateOne',
            'tests.cases.InitialState -(from_root)> collection.sub_collection.TplStateOne',
            'tests.cases.InitialState -(tempo)> state_machine_crawler.state_machine_crawler.EntryPoint',
            'tests.cases.StateOne -(from_state_one)> tests.cases.StateTwo',
            'tests.cases.StateOne -(reset)> tests.cases.StateOne',
            'tests.cases.StateOne -(tempo)> state_machine_crawler.state_machine_crawler.EntryPoint',
            'tests.cases.StateTwo -(tempo)> state_machine_crawler.state_machine_crawler.EntryPoint'])
