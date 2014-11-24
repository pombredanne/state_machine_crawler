import unittest

import mock

from state_machine_crawler import State, StateMachineCrawler, Transition, StateMachineCrawlerError, ErrorTransition
from state_machine_crawler.state_machine_crawler import _create_transition_map, _find_shortest_path


class CustomErrorTransition(ErrorTransition):

    def move(self):
        self._system.error()


class EnterTransition(Transition):

    def move(self):
        self._system.enter()


class UniqueTransition(Transition):

    def move(self):
        self._system.unique()


class NonUniqueTransition(Transition):

    def move(self):
        self._system.non_unique()


class InitialState(State):
    pass


class UnknownState(State):
    pass


class StateOne(State):
    from_initial_state = UniqueTransition.link(source_state=InitialState)


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


class BaseFunctionsTest(unittest.TestCase):

    def test_create_transition_map(self):
        self.assertEqual(_create_transition_map(InitialState), {
            InitialState: {StateOne},
            StateOne: {StateTwo},
            StateTwo: {StateThreeVariantOne, StateThreeVariantTwo},
            StateThreeVariantOne: {StateFour},
            StateThreeVariantTwo: {StateFour},
            StateFour: set()
        })

    def test_find_shortest_path(self):
        graph = _create_transition_map(InitialState)
        shortest_path = _find_shortest_path(graph, InitialState, StateFour)
        self.assertEqual(shortest_path, [InitialState, StateOne, StateTwo, StateThreeVariantTwo, StateFour])


class TestStateMachine(unittest.TestCase):

    def setUp(self):
        self.target = mock.Mock()
        self.smc = StateMachineCrawler(self.target, EnterTransition.link(InitialState), CustomErrorTransition)

    def test_move(self):
        self.smc.move(StateFour)
        self.assertEqual(self.target.enter.call_count, 1)
        self.assertEqual(self.target.unique.call_count, 3)
        self.assertEqual(self.target.non_unique.call_count, 1)

    def test_sequential_moves(self):
        self.assertIs(self.smc.state, None)
        self.smc.move(InitialState)
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
        self.assertRaises(StateMachineCrawlerError, self.smc.move, UnknownState)

    def test_undefined_initial_state(self):
        self.assertRaises(StateMachineCrawlerError, StateMachineCrawler, self.target, EnterTransition,
                          CustomErrorTransition)

    # def test_error_transition(self):
    #     self.target.unique.side_effect = Exception("Woooooo!")
    #     self.smc.start()
    #     print self.smc._current_state
    #     self.smc.move(StateTwo)
    #     self.assertIs(self.smc.state, InitialState)
    #     self.assertEqual(self.target.error.call_count, 1)
