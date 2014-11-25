import unittest

import mock

from state_machine_crawler import Transition, StateMachineCrawler, DeclarationError, TransitionError, State as BaseState
from state_machine_crawler.state_machine_crawler import _create_transition_map, _find_shortest_path


class State(BaseState):

    def verify(self):
        return self._system.ok()


class InitialState(State):
    pass


class InitialTransition(Transition):
    target_state = InitialState

    def move(self):
        self._system.enter()


class UniqueTransition(Transition):

    def move(self):
        self._system.unique()


class NonUniqueTransition(Transition):

    def move(self):
        self._system.non_unique()


class UnknownState(State):
    pass


class StateOne(State):
    from_initial_state = UniqueTransition.link(source_state=InitialState)

    class reset_transition(Transition):
        target_state = "self"

        def move(self):
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


class BaseFunctionsTest(unittest.TestCase):

    def test_create_transition_map(self):
        self.assertEqual(_create_transition_map(InitialState), {
            InitialState: {StateOne},
            StateOne: {StateTwo, StateOne},
            StateTwo: {StateThreeVariantOne, StateThreeVariantTwo},
            StateThreeVariantOne: {StateFour},
            StateThreeVariantTwo: {StateFour},
            StateFour: set()
        })

    def test_find_shortest_path(self):
        graph = _create_transition_map(InitialState)
        shortest_path = _find_shortest_path(graph, InitialState, StateFour)
        self.assertEqual(shortest_path, [InitialState, StateOne, StateTwo, StateThreeVariantTwo, StateFour])


class TestStateMachineTransition(unittest.TestCase):

    def setUp(self):
        self.target = mock.Mock()
        self.smc = StateMachineCrawler(self.target, InitialTransition)

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
        self.assertRaises(TransitionError, self.smc.move, UnknownState)

    def test_reset_the_state(self):
        self.smc.move(StateOne)
        self.assertEqual(self.target.reset.call_count, 0)
        self.smc.move(StateOne)
        self.assertEqual(self.target.reset.call_count, 1)

    def test_state_verification_failure(self):
        self.smc.move(InitialState)
        self.target.ok.return_value = False
        self.assertRaisesRegexp(TransitionError, "Move to state .+ has failed", self.smc.move, StateOne)

    def test_initial_state_verification_failure(self):
        self.target.ok.return_value = False
        self.assertRaisesRegexp(TransitionError, "Getting to the initial state has failed", self.smc.move, InitialState)


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
