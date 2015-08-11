import time

from state_machine_crawler import State as BaseState, transition, StateMachineCrawler


EXEC_TIME = 0


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
