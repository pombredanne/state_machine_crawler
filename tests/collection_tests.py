import unittest

from state_machine_crawler import StateMachineCrawler, StateCollection

from .cases import ALL_STATES, InitialState, StateOne, StateTwo
from .tpl_cases import TplStateOne, TplStateTwo
from . import non_tpl_cases
from .utils import print_struct
from . import solo_tpl_state


class TestCollections(unittest.TestCase):

    def _get_raw_state(self, smc):
        rval = smc.as_graph()

        for state_name, info in rval.iteritems():
            for key in ["next", "current", "failed", "visited", "_entry", "name"]:
                info.pop(key, None)
            for trans, data in info["transitions"].iteritems():
                for key in ["visited", "cost", "failed", "_entry", "target", "source", "current"]:
                    data.pop(key, None)

        return rval

    def test_dict(self):
        smc = StateMachineCrawler(None, InitialState)
        for state in ALL_STATES:
            smc.register_state(state)

        rval = self._get_raw_state(smc)

        print_struct(rval)

        self.assertEqual(rval, {
            "tests.cases.StateThreeVariantTwo": {
                "transitions": {
                    "tests.cases.StateFour": {
                        "name": "from_v2"
                    }
                }
            },
            "tests.cases.InitialState": {
                "transitions": {
                    "tests.cases.StateOne": {
                        "name": "from_initial_state"
                    }
                }
            },
            "tests.cases.StateTwo": {
                "transitions": {
                    "tests.cases.StateThreeVariantOne": {
                        "name": "move"
                    },
                    "tests.cases.StateThreeVariantTwo": {
                        "name": "from_state_two"
                    }
                }
            },
            "tests.cases.StateFour": {
                "transitions": {
                }
            },
            "state_machine_crawler.state_machine_crawler.EntryPoint": {
                "transitions": {
                    "tests.cases.InitialState": {
                        "name": "init"
                    }
                }
            },
            "tests.cases.StateOne": {
                "transitions": {
                    "tests.cases.StateTwo": {
                        "name": "from_state_one"
                    },
                    "tests.cases.StateOne": {
                        "name": "reset"
                    }
                }
            },
            "tests.cases.StateThreeVariantOne": {
                "transitions": {
                    "tests.cases.StateFour": {
                        "name": "from_v1"
                    }
                }
            }
        })

    def test_register_module_custom_name(self):
        smc = StateMachineCrawler(None, InitialState)
        smc.register_collection(StateCollection.from_module(non_tpl_cases, "FooBar"))

        rval = self._get_raw_state(smc)

        print_struct(rval)

        self.assertEqual(rval, {
            "FooBar.TplStateTwo": {
                "transitions": {
                    "tests.cases.StateTwo": {
                        "name": "to_another_unknown_target"
                    }
                }
            },
            "FooBar.TplStateOne": {
                "transitions": {
                    "FooBar.TplStateTwo": {
                        "name": "from_one"
                    },
                    "tests.cases.StateOne": {
                        "name": "to_unknown_target"
                    }
                }
            },
            "tests.cases.InitialState": {
                "transitions": {
                    "FooBar.TplStateOne": {
                        "name": "from_root"
                    },
                    "tests.cases.StateOne": {
                        "name": "from_initial_state"
                    }
                }
            },
            "tests.cases.StateTwo": {
                "transitions": {
                }
            },
            "state_machine_crawler.state_machine_crawler.EntryPoint": {
                "transitions": {
                    "tests.cases.InitialState": {
                        "name": "init"
                    }
                }
            },
            "tests.cases.StateOne": {
                "transitions": {
                    "tests.cases.StateTwo": {
                        "name": "from_state_one"
                    },
                    "tests.cases.StateOne": {
                        "name": "reset"
                    }
                }
            }
        })

    def test_multilayer_collection(self):
        sub_collection = StateCollection("sub_collection", {
            "unknown_target": StateOne,
            "another_unknown_target": StateTwo
        })
        sub_collection.register_state(TplStateOne)
        sub_collection.register_state(TplStateTwo)

        another_sub_collection = StateCollection("another_sub_collection", {
            "unknown_target": StateTwo,
            "another_unknown_target": StateOne
        })
        another_sub_collection.register_state(TplStateOne)
        another_sub_collection.register_state(TplStateTwo)

        collection = StateCollection("collection")
        collection.register_collection(sub_collection)
        collection.register_collection(another_sub_collection)

        smc = StateMachineCrawler(None, InitialState)
        smc.register_collection(collection)

        rval = self._get_raw_state(smc)

        print_struct(rval)

        self.assertEqual(rval, {
            "tests.cases.InitialState": {
                "transitions": {
                    "collection.another_sub_collection.TplStateOne": {
                        "name": "from_root"
                    },
                    "tests.cases.StateOne": {
                        "name": "from_initial_state"
                    },
                    "collection.sub_collection.TplStateOne": {
                        "name": "from_root"
                    }
                }
            },
            "collection.another_sub_collection.TplStateOne": {
                "transitions": {
                    "tests.cases.StateTwo": {
                        "name": "to_unknown_target"
                    },
                    "collection.another_sub_collection.TplStateTwo": {
                        "name": "from_one"
                    }
                }
            },
            "tests.cases.StateTwo": {
                "transitions": {
                }
            },
            "collection.sub_collection.TplStateTwo": {
                "transitions": {
                    "tests.cases.StateTwo": {
                        "name": "to_another_unknown_target"
                    }
                }
            },
            "state_machine_crawler.state_machine_crawler.EntryPoint": {
                "transitions": {
                    "tests.cases.InitialState": {
                        "name": "init"
                    }
                }
            },
            "tests.cases.StateOne": {
                "transitions": {
                    "tests.cases.StateTwo": {
                        "name": "from_state_one"
                    },
                    "tests.cases.StateOne": {
                        "name": "reset"
                    }
                }
            },
            "collection.another_sub_collection.TplStateTwo": {
                "transitions": {
                    "tests.cases.StateOne": {
                        "name": "to_another_unknown_target"
                    }
                }
            },
            "collection.sub_collection.TplStateOne": {
                "transitions": {
                    "tests.cases.StateOne": {
                        "name": "to_unknown_target"
                    },
                    "collection.sub_collection.TplStateTwo": {
                        "name": "from_one"
                    }
                }
            }
        })

    def test_multilayer_top_level_collections(self):

        smc = StateMachineCrawler(None, InitialState)

        smc.register_collection(StateCollection.from_module(solo_tpl_state, "One", {
            "LaunchedState": StateOne
        }))
        smc.register_collection(StateCollection.from_module(solo_tpl_state, "Two", {
            "LaunchedState": StateTwo
        }))

        rval = self._get_raw_state(smc)

        print_struct(rval)

        self.assertEqual(rval, {
            "One.SoloTplState": {
                "transitions": {
                    "tests.cases.StateOne": {
                        "name": "back"
                    }
                }
            },
            "tests.cases.InitialState": {
                "transitions": {
                    "tests.cases.StateOne": {
                        "name": "from_initial_state"
                    }
                }
            },
            "tests.cases.StateTwo": {
                "transitions": {
                    "Two.SoloTplState": {
                        "name": "there"
                    }
                }
            },
            "Two.SoloTplState": {
                "transitions": {
                    "tests.cases.StateTwo": {
                        "name": "back"
                    }
                }
            },
            "state_machine_crawler.state_machine_crawler.EntryPoint": {
                "transitions": {
                    "tests.cases.InitialState": {
                        "name": "init"
                    }
                }
            },
            "tests.cases.StateOne": {
                "transitions": {
                    "tests.cases.StateTwo": {
                        "name": "from_state_one"
                    },
                    "One.SoloTplState": {
                        "name": "there"
                    },
                    "tests.cases.StateOne": {
                        "name": "reset"
                    }
                }
            }
        })
