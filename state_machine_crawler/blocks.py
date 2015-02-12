from inspect import isclass
from abc import ABCMeta, abstractmethod

from .errors import DeclarationError


class Transition(object):
    """ Represents a transformation of the system from one state into another

    Transitions have a *_system* attribute that represents the entity with which transitions' states are associated.

    Class definitions of the transitions must have:

    cost (int)
        Relative *price* of the transition. Transitions that take longer time to run are more *expensive*. The *cost*
        has to be experimentally determined.
    target_state (subclass of :class:`State <state_machine_crawler.State>` or string "self")
        The state to which the system should be transitioned, if "self" is used the transition is done to the holder
        class itself
    source_state (subclass of :class:`State <state_machine_crawler.State>`)
        The state from which the system should be transitioned

    The only difference between *target_state* and *source_state* is a direction of the relationship.

    Note: there can be only *target_state* or only *source_state* because if a transition from state **A** to state
    **B** is possible it does not at all imply that the opposite transition can be performed the same way.
    """
    __metaclass__ = ABCMeta
    cost = 1
    target_state = source_state = None

    def __init__(self, system):
        self._system = system

    @abstractmethod
    def move(self):
        """
        Performs the actions to move from one state to another.
        """

    @classmethod
    def link(cls, target_state=None, source_state=None):
        """
        Links an existing transition with a specific state.

        This method exists to avoid creating unnecessary subclasses in the situation when multiple states can perform
        similar transitions.
        """
        tstate = target_state
        sstate = source_state

        class NewTransition(cls):
            target_state = tstate or cls.target_state
            source_state = sstate or cls.source_state
        return NewTransition


class StateMetaClass(ABCMeta):

    def __init__(self, name, bases, attrs):
        super(StateMetaClass, self).__init__(name, bases, attrs)
        self.transition_map = {}
        self.full_name = self.__module__ + "." + self.__name__
        for name in dir(self):
            attr = getattr(self, name)

            if not (isclass(attr) and issubclass(attr, Transition)):
                continue

            class TempTransition(attr):
                target_state = self if attr.target_state == "self" else attr.target_state
            TempTransition.__name__ = name

            attr = TempTransition
            setattr(self, name, TempTransition)

            if attr.target_state:
                attr.source_state = self
                self.transition_map[attr.target_state] = attr
            elif attr.source_state:
                class RelatedTransition(TempTransition):
                    target_state = self
                attr.source_state.transition_map[self] = RelatedTransition
            else:
                raise DeclarationError("No target nor source state is defined for %r" % attr)


class State(object):
    """ A base class for any state of the system

    States have a *_system* attribute that represents the entity with which they are associated.
    """
    __metaclass__ = StateMetaClass

    def __init__(self, system):
        self._system = system

    @abstractmethod
    def verify(self):
        """
        Checks if the system ended up in a desired state. Should return a boolean indicating if verification went well
        or not.
        """
