import unittest
import re
from datetime import datetime as dt
import pandas as pd

from src.core.io.file_utils import FileUtils
FileUtils.update_config('./config.json')
import src.core.io.config as hc

from src.analyses.sequence_detection.shared.containers import ExtendedCourse, SequenceGraph
from src.core.algorithms.sequence.format import SequenceInformation
from tests.sequences.test_containers.mock_code_converter import MockCodeConverter

class MockCourse:
    def __init__(self, sequence):
        timestamps = list(range(len(sequence)))
        seq = SequenceInformation(sequence, timestamps, [], [])
        self.item_sequence = seq

class SequenceFlagTest(unittest.TestCase):
    def setUp(self):
        self.cdv = MockCodeConverter()
        self.courses = []
        for sequence in [
            ["1", "2 3", "4", '5', '7', '1 3', '4', '8'],
            ["1", "1", "2 3", "4"]
        ]:
            mock = MockCourse(sequence)
            course = ExtendedCourse(mock)
            self.courses.append(course)

        self.rules = {}
        for rule in [
            "1_2_4",
            "1_2 3_4",
            "1_1 3_4",
            "7_1 3_4",
            "2_1_5_4 6"
        ]:
            rule_graph = SequenceGraph.from_rule_name(rule, self.cdv.get_mbs_item_fee)
            self.rules[rule] = rule_graph

    def test_sequence_flags(self):
        rare_items = ["8"]
        rare_item_costs = {x: self.cdv.get_mbs_item_fee(x)[0] for x in rare_items}
        rule_names_by_length = {}
        for rule, graph in self.rules.items():
            current = rule_names_by_length.get(graph.total_items, [])
            current.append(rule)
            rule_names_by_length[graph.total_items] = current

        rule_frequencies = {x: {"75": 0.5, "25": 0.4} for x in self.rules}
        rule_ontologies = {x: re.sub('\d', '%d', x) for x in self.rules} # set all to same ontology

        rule_frequencies["1_1 3_4"]["75"] = 0.6
        expected_flags = [
            [0, 1, 2, 4, 5, 6, 7],
            [1, 2, 3]
        ]
        expected_double_flags = [
            [1, 4, 7],
            [2]
        ]
        expected_costs = [(2**2 - 2**1)+ (2**7 - 2**1) + 2**8, 2**2 - 2**1]
        filtered_rules = {x: y for x, y in self.rules.items() if x in ["1_2 3_4", "7_1 3_4"]}
        for i, course in enumerate(self.courses):
            for x in rare_items:
                course.label_rare_items(x, rare_item_costs)

            for rule in filtered_rules.values():
                rule.find_overclaimed_item_for_provider("test", 0.5, rule_names_by_length, self.rules, rule_frequencies, rule_ontologies)
                course.process_sequence_graph("test", rule)

            unusual_course_cost = course.get_unusual_course_costs()
            self.assertEqual(len(course.flagged_timestamps), len(expected_flags[i]))
            self.assertEqual(len(course.double_flagged_timestamps), len(expected_double_flags[i]))
            self.assertEqual(unusual_course_cost, expected_costs[i])
            for j, val in enumerate(course.flagged_timestamps):
                self.assertEqual(val, expected_flags[i][j])

            for j, val in enumerate(course.double_flagged_timestamps):
                self.assertEqual(val, expected_double_flags[i][j])

