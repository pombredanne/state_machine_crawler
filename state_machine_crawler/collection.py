from .errors import DeclarationError
from .blocks import State


class StateCollection(object):

    def __init__(self, name):
        self._name = name
        self._states = set()
        self._collections = set()

    def register_state(self, state):
        if not issubclass(state, State):
            raise DeclarationError("{0} must be a State subclass".format(state))
        self._states.add(state)

    def register_collection(self, collection):
        if not isinstance(collection, StateCollection):
            raise DeclarationError("{0} must be a StateCollection instance".format(collection))
        self._collections.add(collection)

    def populate_templates(self, context):
        """
        @context (dict)
            mapping between string values and concrete state specifically for this collection usecase
        """
        # TODO: create a new collection of states with string names replaced with proper State subclasses
        return self._states
