from .errors import DeclarationError
from .blocks import State


class StateCollection(object):

    def __init__(self, name):
        self._name = name
        self._states = set()
        self._collections = set()

    def register_state(self, state):
        """ Add a state to a collection """
        if not issubclass(state, State):
            raise DeclarationError("{0} must be a State subclass".format(state))
        self._states.add(state)

    def register_collection(self, collection):
        """ Add a subcollection """
        if not isinstance(collection, StateCollection):
            raise DeclarationError("{0} must be a StateCollection instance".format(collection))
        self._collections.add(collection)

    @property
    def states(self):
        return self._states

    @property
    def collections(self):
        return self._collections
