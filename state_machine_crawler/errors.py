class StateMachineError(Exception):
    """ Base error to be raise by the toolkit """


class TransitionError(StateMachineError):
    """ Raised if the transition or verification fails """


class UnreachableStateError(StateMachineError):
    """ Raised if state is not reachable """


class DeclarationError(StateMachineError):
    """ Raised if something is wrong with the state machine declaration in general """
