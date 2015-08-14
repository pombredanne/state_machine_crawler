import inspect

from .errors import DeclarationError
from .blocks import State, transition


class StateCollection(object):
    """
    name (string=None)
        Collection name. Defaults to module name.
    context_map (dict)
        A mapping between state entry points and the actual states.

    In some cases there is a need to join a bunch of states coming from different modules into a single logical unit.

    In order to achieve this declare a collection, add a bunch of states to it and register the collection to a
    state machine:

    .. code:: python

        ...

        collection = StateCollection("My collection")
        collection.register_state(StateOne)
        collection.register_state(StateTwo)

        scm.register_collection(collection)

    Once joined into a collection, states shall be shown as logical cluster in a webview.

    Apart from entirely decorational use, there is also a practical usecase.

    States can be declared with entry points for their transitions:

    .. code:: python

        ...

        class SampleState(State):

            @transition(source_state="initial_state")
            def move(self):
                ...

        collection_one = StateCollection("one", {
            "initial_state": StateOne
        })

        collection_two = StateCollection("one", {
            "initial_state": StateTwo
        })

    If the entry points are used as above the framework creates two subclasses of SampleState. One with StateOne
    as a source for the *move* transition and one with StateTwo.
    """

    def __init__(self, name, context_map=None):
        self._name = name
        self._states = set()
        self._context_map = dict(context_map or {})
        self._related_states = set(self._context_map.values())
        self._collections = {}

    @property
    def name(self):
        return self._name

    def register_state(self, state):
        """
        Adds a state to a collection

        state
            :class:`State <state_machine_crawler.State>` subclass

        """
        if not issubclass(state, State):
            raise DeclarationError("{0} must be a State subclass".format(state))
        self._states.add(state)

    def register_collection(self, collection):
        """
        Adds a subcollection

        collection
            :class:`StateCollection <state_machine_crawler.StateCollection>` subclass
        """
        if not isinstance(collection, StateCollection):
            raise DeclarationError("{0} must be a StateCollection instance".format(collection))
        collection._context_map.update(self._context_map)
        self._collections[collection.name] = collection

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

        for col in self._collections.itervalues():
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
        returns (set)
            states that do not directly belong to the collection but are referenced from the inside one way or another.
        """
        states = set()
        for state in self._related_states:
            states.add(state)
        for col in self._collections.itervalues():
            for state in col.related_states:
                states.add(state)
        return states

    @classmethod
    def from_module(cls, module, name=None, context_map=None):
        """
        Creates a collection from a module.

        module (Python module)
            All State subclasses from this module are added to the collection.

        name, context_map
            See constructor

        .. code:: python

            collection = StateCollection(sample_module, "Given name", {
                "Entry point": SampleStateOne,
                "Other entry point": SampleStateTwo
            })

        """

        module_collection = cls(name or module.__name__, context_map=context_map)
        for name in dir(module):
            if name.startswith("_"):
                continue
            item = getattr(module, name)

            if inspect.isclass(item) and issubclass(item, State):
                if item.__module__ == module.__name__:
                    module_collection.register_state(item)
        return module_collection
