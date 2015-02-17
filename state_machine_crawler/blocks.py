from abc import ABCMeta, abstractmethod

from .errors import DeclarationError


def transition(source_state=None, target_state=None, cost=1):
    """

    Represents a process of moving from source_state to target_state

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

    def wrap(function):
        def wraped_f(state_instance):
            function(state_instance)
        wraped_f.source_state = source_state
        wraped_f.target_state = target_state
        wraped_f.cost = cost
        setattr(wraped_f, "@transition@", True)
        return wraped_f

    return wrap


class StateMetaClass(ABCMeta):

    def __init__(self, name, bases, attrs):
        super(StateMetaClass, self).__init__(name, bases, attrs)
        self.transition_map = {}
        self.full_name = self.__module__ + "." + self.__name__
        for name in dir(self):
            attr = getattr(self, name)

            if not hasattr(attr, "@transition@"):
                continue

            if attr.target_state == "self":
                target = self
            else:
                target = attr.target_state

            source = attr.source_state

            def _ver(item):
                return item and item.__name__.startswith("_")

            if _ver(target) or _ver(self) or _ver(source):
                continue

            if source and target:
                raise DeclarationError("Only target or source state can be defined for %r " % attr)
            elif target:
                self.transition_map[target] = attr
            elif source:
                attr.source_state.transition_map[self] = attr
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
