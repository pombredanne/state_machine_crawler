from state_machine_crawler import transition

from . import cases


class TplStateOne(cases.State):

    @transition(source_state=cases.InitialState)
    def from_root(self):
        pass

    @transition(target_state=cases.StateOne)
    def to_unknown_target(self):
        pass


class TplStateTwo(cases.State):

    @transition(source_state=TplStateOne)
    def from_one(self):
        pass

    @transition(target_state=cases.StateTwo)
    def to_another_unknown_target(self):
        pass
