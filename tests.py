import unittest
import time

import mock

from state_machine_crawler import Transition, StateMachineCrawler, DeclarationError, TransitionError, \
    State as BaseState, GraphMonitor
from state_machine_crawler.state_machine_crawler import _create_transition_map, _find_shortest_path

# set to time in seconds to configure duration of each transition and verification
EXEC_TIME = 0.0


class State(BaseState):

    def verify(self):
        time.sleep(EXEC_TIME)
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


class BaseFunctionsTest(unittest.TestCase):

    def test_create_transition_map(self):

        rval = {}
        for key, value in _create_transition_map(InitialTransition).iteritems():
            if key.__name__ == "EntryPoint":
                continue
            rval[key] = value

        self.assertEqual({
            InitialState: {StateOne, InitialState},
            StateOne: {StateTwo, StateOne, InitialState},
            StateTwo: {StateThreeVariantOne, StateThreeVariantTwo, InitialState},
            StateThreeVariantOne: {StateFour, InitialState},
            StateThreeVariantTwo: {StateFour, InitialState},
            StateFour: {InitialState}
        }, rval)

    def test_find_shortest_path(self):
        graph = _create_transition_map(InitialTransition)
        shortest_path = _find_shortest_path(graph, InitialState, StateFour)
        self.assertEqual(shortest_path, [InitialState, StateOne, StateTwo, StateThreeVariantTwo, StateFour])


class BaseTestStateMachineTransitionCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.target = mock.Mock()
        cls.smc = StateMachineCrawler(cls.target, InitialTransition)
        if EXEC_TIME:
            cls.monitor = GraphMonitor("state-crawler-tests", None)
            cls.monitor.crawler = cls.smc
            cls.smc.set_on_state_change_handler(cls.monitor)
            cls.monitor.start()

    @classmethod
    def tearDownClass(cls):
        if EXEC_TIME:
            cls.monitor.stop()


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


class TestStateMachineWithStateAutoconfig(unittest.TestCase):

    def test_autostate(self):

        system = {"state_flag": 666}

        class NotACurrentState(State):

            def verify(self):
                return system["state_flag"] == 13

            class init(Transition):
                target_state = "self"

                def move(self):
                    pass

        class AnotherNotACurrentState(State):

            def verify(self):
                return system["state_flag"] == 6

            class from_start(Transition):
                source_state = NotACurrentState

                def move(self):
                    pass

        class CurrentState(State):

            def verify(self):
                return system["state_flag"] == 666

            class from_another_state(Transition):
                source_state = AnotherNotACurrentState

                def move(self):
                    pass

        smc = StateMachineCrawler.create(system, NotACurrentState.init)
        self.assertIs(smc._current_state, CurrentState)

    def test_autostate_with_furthermost_state(self):

        system = {"state_flag": 666}

        class NotACurrentState(State):

            def verify(self):
                return system["state_flag"] == 13

            class init(Transition):
                target_state = "self"

                def move(self):
                    pass

        class AnotherNotACurrentState(State):

            def verify(self):
                return system["state_flag"] == 666

            class from_start(Transition):
                source_state = NotACurrentState

                def move(self):
                    pass

        class CurrentState(State):

            def verify(self):
                return system["state_flag"] == 666

            class from_another_state(Transition):
                source_state = AnotherNotACurrentState

                def move(self):
                    pass

        smc = StateMachineCrawler.create(system, NotACurrentState.init)
        self.assertIs(smc._current_state, CurrentState)

    def test_autostate_conflict(self):

        system = {"state_flag": 666}

        class NotACurrentState(State):

            def verify(self):
                return system["state_flag"] == 13

            class init(Transition):
                target_state = "self"

                def move(self):
                    pass

        class AnotherNotACurrentState(State):

            def verify(self):
                return system["state_flag"] == 6

            class from_start(Transition):
                source_state = NotACurrentState

                def move(self):
                    pass

        class CurrentState(State):

            def verify(self):
                return system["state_flag"] == 666

            class from_another_state(Transition):
                source_state = AnotherNotACurrentState

                def move(self):
                    pass

        class ConflictingState(State):

            def verify(self):
                return system["state_flag"] == 666

            class from_another_state(Transition):
                source_state = AnotherNotACurrentState

                def move(self):
                    pass

        self.assertRaisesRegexp(TransitionError, "States .+ and .+ satisfy system's condition",
                                StateMachineCrawler.create, system, NotACurrentState.init)
