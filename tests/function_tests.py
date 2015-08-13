from copy import deepcopy
import unittest

from state_machine_crawler.serializers.hierarchy import create_hierarchy

from .utils import print_struct


INPUT = {
    "tests.cases.InitialState": {
        "name": "tests.cases.InitialState",
        "next": False,
        "current": False,
        "failed": False,
        "visited": False,
        "transitions": {
            "tests.cases.StateOne": {
                "target": "tests.cases.StateOne",
                "failed": False,
                "cost": 1,
                "visited": False,
                "_entry": "ENTRY",
                "name": "from_initial_state"
            },
            "collection.another_sub_collection.TplStateOne": {
                "target": "collection.another_sub_collection.TplStateOne",
                "failed": False,
                "cost": 1,
                "visited": False,
                "_entry": "ENTRY",
                "name": "from_root"
            }
        },
        "_entry": "ENTRY",
    },
    "collection.another_sub_collection.TplStateOne": {
        "name": "collection.another_sub_collection.TplStateOne",
        "next": False,
        "current": False,
        "failed": False,
        "visited": False,
        "transitions": {
            "tests.cases.StateTwo": {
                "target": "tests.cases.StateTwo",
                "failed": False,
                "cost": 1,
                "visited": False,
                "_entry": "ENTRY",
                "name": "to_unknown_target"
            },
            "collection.another_sub_collection.TplStateTwo": {
                "target": "collection.another_sub_collection.TplStateTwo",
                "failed": False,
                "cost": 1,
                "visited": False,
                "_entry": "ENTRY",
                "name": "from_one"
            }
        },
        "_entry": "ENTRY",
    },
    "tests.cases.StateTwo": {
        "name": "tests.cases.StateTwo",
        "next": False,
        "current": False,
        "failed": False,
        "visited": False,
        "transitions": {
        },
        "_entry": "ENTRY",
    },
    "collection.sub_collection.TplStateTwo": {
        "name": "collection.sub_collection.TplStateTwo",
        "next": False,
        "current": False,
        "failed": False,
        "visited": False,
        "transitions": {
            "tests.cases.StateTwo": {
                "target": "tests.cases.StateTwo",
                "failed": False,
                "cost": 1,
                "visited": False,
                "_entry": "ENTRY",
                "name": "to_another_unknown_target"
            }
        },
        "_entry": "ENTRY",
    },
    "state_machine_crawler.state_machine_crawler.EntryPoint": {
        "name": "state_machine_crawler.state_machine_crawler.EntryPoint",
        "next": False,
        "current": True,
        "failed": False,
        "visited": True,
        "transitions": {
            "tests.cases.InitialState": {
                "target": "tests.cases.InitialState",
                "failed": False,
                "cost": 1,
                "visited": False,
                "_entry": "ENTRY",
                "name": "init"
            }
        },
        "_entry": "ENTRY",
    },
    "tests.cases.StateOne": {
        "name": "tests.cases.StateOne",
        "next": False,
        "current": False,
        "failed": False,
        "visited": False,
        "transitions": {
            "tests.cases.StateOne": {
                "target": "tests.cases.StateOne",
                "failed": False,
                "cost": 1,
                "visited": False,
                "_entry": "ENTRY",
                "name": "reset"
            },
            "tests.cases.StateTwo": {
                "target": "tests.cases.StateTwo",
                "failed": False,
                "cost": 1,
                "visited": False,
                "_entry": "ENTRY",
                "name": "from_state_one"
            }
        },
        "_entry": "ENTRY",
    },
    "collection.another_sub_collection.TplStateTwo": {
        "name": "collection.another_sub_collection.TplStateTwo",
        "next": False,
        "current": False,
        "failed": False,
        "visited": False,
        "transitions": {
            "tests.cases.StateOne": {
                "target": "tests.cases.StateOne",
                "failed": False,
                "cost": 1,
                "visited": False,
                "_entry": "ENTRY",
                "name": "to_another_unknown_target"
            }
        },
        "_entry": "ENTRY",
    },
    "collection.sub_collection.TplStateOne": {
        "name": "collection.sub_collection.TplStateOne",
        "next": False,
        "current": False,
        "failed": False,
        "visited": False,
        "transitions": {
            "tests.cases.StateOne": {
                "target": "tests.cases.StateOne",
                "failed": False,
                "cost": 1,
                "visited": False,
                "_entry": "ENTRY",
                "name": "to_unknown_target"
            },
            "collection.sub_collection.TplStateTwo": {
                "target": "collection.sub_collection.TplStateTwo",
                "failed": False,
                "cost": 1,
                "visited": False,
                "_entry": "ENTRY",
                "name": "from_one"
            }
        },
        "_entry": "ENTRY",
    }
}


class TestHierarchy(unittest.TestCase):

    def _get_clean(self, rval):

        rval = deepcopy(rval)

        for state_name, info in rval.iteritems():
            for key in ["next", "current", "failed", "visited", "_entry", "name"]:
                info.pop(key, None)
            for trans, data in info["transitions"].iteritems():
                for key in ["visited", "cost", "failed", "_entry", "target", "source", "current"]:
                    data.pop(key, None)

        return rval

    def test_hierarchy(self):
        hierarchy = create_hierarchy(self._get_clean(INPUT))

        print_struct(hierarchy)

        self.assertEqual(hierarchy, {
            "tests": {
                "cases": {
                    "StateTwo": {
                        "transitions": {
                        }
                    },
                    "StateOne": {
                        "transitions": {
                            "tests.cases.StateTwo": {
                                "name": "from_state_one"
                            },
                            "tests.cases.StateOne": {
                                "name": "reset"
                            }
                        }
                    },
                    "InitialState": {
                        "transitions": {
                            "collection.another_sub_collection.TplStateOne": {
                                "name": "from_root"
                            },
                            "tests.cases.StateOne": {
                                "name": "from_initial_state"
                            }
                        }
                    }
                }
            },
            "state_machine_crawler": {
                "state_machine_crawler": {
                    "EntryPoint": {
                        "transitions": {
                            "tests.cases.InitialState": {
                                "name": "init"
                            }
                        }
                    }
                }
            },
            "collection": {
                "sub_collection": {
                    "TplStateTwo": {
                        "transitions": {
                            "tests.cases.StateTwo": {
                                "name": "to_another_unknown_target"
                            }
                        }
                    },
                    "TplStateOne": {
                        "transitions": {
                            "tests.cases.StateOne": {
                                "name": "to_unknown_target"
                            },
                            "collection.sub_collection.TplStateTwo": {
                                "name": "from_one"
                            }
                        }
                    }
                },
                "another_sub_collection": {
                    "TplStateTwo": {
                        "transitions": {
                            "tests.cases.StateOne": {
                                "name": "to_another_unknown_target"
                            }
                        }
                    },
                    "TplStateOne": {
                        "transitions": {
                            "tests.cases.StateTwo": {
                                "name": "to_unknown_target"
                            },
                            "collection.another_sub_collection.TplStateTwo": {
                                "name": "from_one"
                            }
                        }
                    }
                }
            }
        })
