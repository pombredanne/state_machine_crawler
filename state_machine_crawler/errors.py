class StateMachineError(Exception):
    """ Base error to be raise by the toolkit """


class TransitionError(StateMachineError):
    """ Raised if the transition could not be performed.

    Failure could happen because:

    - target state is not reachable
    - state verification failed

    NOTE: if transition itself fails (i.e. exception in the *move* method) - the exception is raised as is
    """


class DeclarationError(StateMachineError):
    """ Raised if something is wrong with the state machine declaration in general """
