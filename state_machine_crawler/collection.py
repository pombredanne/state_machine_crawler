import inspect

from .errors import DeclarationError
from .blocks import State, transition


class StateCollection(object):

    def __init__(self, name, context_map=None):
        self._name = name
        self._states = set()
        self._context_map = dict(context_map or {})
        self._related_states = set(self._context_map.values())
        self._collections = set()

    @property
    def name(self):
        return self._name

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

    def _create_state(self, parent):

        class SubClass(parent):
            pass

        setattr(SubClass, "@subclassed@", True)
        self._context_map[parent] = SubClass

        SubClass.full_name = self._name + "." + parent.__name__

        return SubClass

    def _process_transition(self, state, trans, related_state_ref, state_collection, transition_collection):

        related_state = getattr(trans, related_state_ref)
        if hasattr(related_state, "@subclassed@"):
            return

        contextual = self._context_map.get(related_state)
        if not contextual:
            if related_state == "self":
                contextual = state
            elif isinstance(related_state, basestring):
                raise DeclarationError("No substitution found for {0} in {1} inside {2}".format(
                    related_state, state.full_name, self._name))
            else:
                return
        if related_state in state_collection:
            state_collection.remove(related_state)
        transition_collection.remove(trans)
        kwargs = {related_state_ref: contextual}
        wraped_f = transition(**kwargs)(trans)
        wraped_f.original = getattr(trans, "original", trans)
        transition_collection.append(wraped_f)
        state_collection.append(contextual)

        setattr(state, trans.original.__name__, wraped_f)

    def _process_state(self, state):
        new_transitions = list(state.transitions)

        for item in state.transitions:

            if item.target_state:
                self._process_transition(state, item, "target_state", state.outgoing, new_transitions)
            else:
                self._process_transition(state, item, "source_state", state.incoming, new_transitions)

        state.transitions = new_transitions

    def _contains(self, states, state):
        names = [st.full_name for st in states]
        return state.full_name in names

    def _renamed(self, state):
        return state.full_name != self._name + "." + state.__name__

    @property
    def states(self):
        """
        Returns a set of states registred within a collection
        """
        states = set()
        for state in self._states:
            if state.with_placeholders or self._contains(states, state) or self._renamed(state):
                state = self._create_state(state)
            states.add(state)

        for col in self._collections:
            for state in col.states:
                state.full_name = self._name + "." + state.full_name
                states.add(state)

        for state in states:
            if state.with_placeholders or hasattr(state, "@subclassed@"):
                self._process_state(state)

        return states

    @property
    def related_states(self):
        """
        Returns a set of states that do not directly belong to the collection but are referenced from the inside one
        way or another.
        """
        states = set()
        for state in self._related_states:
            states.add(state)
        for col in self._collections:
            for state in col.related_states:
                states.add(state)
        return states

    @classmethod
    def from_module(cls, module, name=None, context_map=None):
        module_collection = cls(name or module.__name__, context_map=context_map)
        for name in dir(module):
            if name.startswith("_"):
                continue
            item = getattr(module, name)

            if inspect.isclass(item) and issubclass(item, State):
                if item.__module__ == module.__name__:
                    module_collection.register_state(item)
        return module_collection
