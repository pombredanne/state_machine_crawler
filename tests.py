import unittest

import mock

from state_machine_crawler import State, StateMachineCrawler, Transition, _create_transition_map, _find_shortest_path


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


class TestStateMachine(unittest.TestCase):

    def test_create_transition_map(self):

        self.assertEqual(_create_transition_map(InitialState), {
            InitialState: {StateOne},
            StateOne: {StateTwo},
            StateTwo: {StateThreeVariantOne, StateThreeVariantTwo},
            StateThreeVariantOne: {StateFour},
            StateThreeVariantTwo: {StateFour}
        })

    def test_find_shortest_path(self):
        graph = _create_transition_map(InitialState)
        shortest_path = _find_shortest_path(graph, InitialState, StateFour)
        self.assertEqual(shortest_path, [InitialState, StateOne, StateTwo, StateThreeVariantTwo, StateFour])

    def test_move(self):
        target = mock.Mock()
        smc = StateMachineCrawler(target, EnterTransition.link(InitialState))
        smc.start()
        smc.move(StateFour)
        self.assertEqual(target.enter.call_count, 1)
        self.assertEqual(target.unique.call_count, 3)
        self.assertEqual(target.non_unique.call_count, 1)

    def test_sequential_moves(self):
        target = mock.Mock()
        smc = StateMachineCrawler(target, EnterTransition.link(InitialState))
        smc.start()
        self.assertIs(smc.state, InitialState)
        smc.move(StateOne)
        self.assertIs(smc.state, StateOne)
        smc.move(StateTwo)
        self.assertIs(smc.state, StateTwo)
        smc.move(StateFour)
        self.assertIs(smc.state, StateFour)
