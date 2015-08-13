import unittest

import mock

from state_machine_crawler import StateMachineCrawler
from state_machine_crawler.serializers.dot import Serializer

from .cases import ALL_STATES, InitialState, StateTwo
from .utils import print_struct


# dot -Tpng test.dot -o test.png
DOT_GRAPH = """
digraph StateMachine {
    splines=polyline;
    concentrate=true;
    rankdir=LR;
    state_machine_crawler_state_machine_crawler_EntryPoint [
        style=filled label="+" shape=doublecircle fillcolor=forestgreen fontcolor=white];
    subgraph cluster_2 {
        label="tests";
        color=blue;
        fontcolor=blue;
        subgraph cluster_3 {
            label="cases";
            color=blue;
            fontcolor=blue;
            tests_cases_StateTwo [
                style=filled label="StateTwo" shape=box fillcolor=blue fontcolor=white];
            tests_cases_StateThreeVariantOne [
                style=filled label="StateThreeVariantOne" shape=box fillcolor=white fontcolor=black];
            tests_cases_StateFour [
                style=filled label="StateFour" shape=box fillcolor=white fontcolor=black];
            tests_cases_InitialState [
                style=filled label="InitialState" shape=box fillcolor=forestgreen fontcolor=white];
            tests_cases_StateOne [
                style=filled label="StateOne" shape=box fillcolor=forestgreen fontcolor=white];
            tests_cases_StateThreeVariantTwo [
                style=filled label="StateThreeVariantTwo" shape=box fillcolor=white fontcolor=black];
        }
    }
    tests_cases_StateThreeVariantTwo -> tests_cases_StateFour [
        color=black fontcolor=black label=" "];
    tests_cases_StateOne -> tests_cases_StateOne [
        color=black fontcolor=black label=" "];
    tests_cases_StateOne -> tests_cases_StateTwo [
        color=forestgreen fontcolor=forestgreen label=" "];
    tests_cases_InitialState -> tests_cases_StateOne [
        color=forestgreen fontcolor=forestgreen label=" "];
    state_machine_crawler_state_machine_crawler_EntryPoint -> tests_cases_InitialState [
        color=forestgreen fontcolor=forestgreen label=" "];
    tests_cases_StateThreeVariantOne -> tests_cases_StateFour [
        color=black fontcolor=black label=" "];
    tests_cases_StateTwo -> tests_cases_StateThreeVariantOne [
        color=black fontcolor=black label="$2"];
    tests_cases_StateTwo -> tests_cases_StateThreeVariantTwo [
        color=black fontcolor=black label=" "];
}"""


class TestStateMachineSerialization(unittest.TestCase):

    def test_repr(self):
        smc = StateMachineCrawler(mock.Mock(), InitialState)
        for state in ALL_STATES:
            smc.register_state(state)
        smc.move(StateTwo)

        # print_struct(create_hierarchy(smc.as_graph()))

        value = repr(Serializer(smc))
        target_lines = DOT_GRAPH.replace("\n", "").replace("    ", "").replace("}", "};").replace("{", "{;").split(";")
        real_lines = value.replace("}", "};").replace("{", "{;").split(";")

        target_lines = map(str.strip, target_lines)
        real_lines = map(str.strip, real_lines)

        not_expected = []
        for i in real_lines:
            if i not in target_lines:
                not_expected.append(i)

        not_in_target = []
        for i in target_lines:
            if i not in real_lines:
                not_in_target.append(i)

        print "NOT IN RELITY ************"
        print_struct(sorted(not_in_target))
        print "NOT EXPECTED ************"
        print_struct(sorted(not_expected))

        self.assertEqual(sorted(real_lines), sorted(target_lines))
