class StateMachineError(Exception):
    """ Base error to be raise by the toolkit """


class TransitionError(StateMachineError):
    """ Raised if the transition or verification fails """


class UnreachableStateError(StateMachineError):
    """ Raised if state is not reachable """


class NonExistentStateError(StateMachineError):
    """ Raised when the transition is done to a state that was not registered """


class DeclarationError(StateMachineError):
    """ Raised if something is wrong with the state machine declaration in general """


class MultipleStatesError(StateMachineError):
    """ Raised when finding multiple states to transition to with a certain search criteria """
