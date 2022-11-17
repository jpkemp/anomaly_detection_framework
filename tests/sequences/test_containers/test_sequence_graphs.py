import re
import unittest
from datetime import datetime as dt
import pandas as pd

from src.core.io.file_utils import FileUtils
FileUtils.update_config('./config.json')
import src.core.io.config as hc

from src.analyses.sequence_detection.shared.containers.sequence_graph import SequenceGraph
from tests.sequences.test_containers.mock_code_converter import MockCodeConverter

cdv = MockCodeConverter().get_mbs_item_fee
class TestSequenceGraph(unittest.TestCase):
    def test_sequence_graph(self):
        # check distance
        x = SequenceGraph.from_rule_name("1_2 3_4", cdv)
        x_same_length_not_similar = SequenceGraph.from_rule_name("1_1 2_2", cdv)
        x_same_length_similar = SequenceGraph.from_rule_name("1_1 3_4", cdv)
        x_super_duper_parent = SequenceGraph.from_rule_name("1", cdv)
        x_super_parent = SequenceGraph.from_rule_name("1_2", cdv)
        x_parent_same = SequenceGraph.from_rule_name("1_2_4", cdv)
        x_parent_diff = SequenceGraph.from_rule_name("1_2 3", cdv)
        not_x_parent = SequenceGraph.from_rule_name("4_5 6", cdv)
        y = SequenceGraph.from_rule_name("1_2 3 2 3_4_5 6 6", cdv)
        y_same_length = SequenceGraph.from_rule_name("2_1_5_4 6", cdv)
        z = SequenceGraph.from_rule_name('3', cdv)
        z_other = SequenceGraph.from_rule_name('2', cdv)
        z_other_ontology = SequenceGraph.from_rule_name('7', cdv)
        x_other_ontology = SequenceGraph.from_rule_name("1_7 3_4", cdv)
        self.assertEqual(x.check_distance(y), 5)
        self.assertEqual(y.check_distance(x), 5)
        self.assertEqual(x.check_distance(x_parent_same), 1)
        self.assertEqual(x.check_distance(x_parent_diff), 1)
        self.assertEqual(x.check_distance(x_same_length_similar), 2)
        self.assertEqual(x.check_distance(x_same_length_not_similar), 4)
        self.assertEqual(x.check_distance(not_x_parent), 7)

        # setup
        all_rules = [x,
                     x_super_duper_parent,
                     x_super_parent,
                     x_same_length_not_similar,
                     x_parent_same,
                     x_parent_diff,
                     not_x_parent,
                     x_same_length_similar,
                     y,
                     y_same_length,
                     z,
                     z_other,
                     z_other_ontology,
                     x_other_ontology]
        rule_names_by_length = {}
        rule_names_by_length[4] = []
        for l, rules in [
            (1, [z, z_other, x_super_duper_parent]),
            (2, [x_super_parent]),
            (3, [x_parent_same, x_parent_diff, not_x_parent]),
            (4, [x, x_same_length_not_similar, x_same_length_similar]),
            (5, [y_same_length]),
            (9, [y])
            ]:
            rule_names_by_length[l] = []
            for rule in rules:
                rule_names_by_length[l].append(rule.name)

        sequence_graphs = {}
        for graph in all_rules:
            sequence_graphs[graph.name] = graph

        rule_frequencies = {x: {"75": 0.5, "25": 0.5} for x in sequence_graphs}
        rule_ontologies = {x: re.sub('\d', '%d', x) for x in sequence_graphs} # set all to same ontology
        rule_ontologies[z_other_ontology.name] = '%x'
        rule_ontologies[x_other_ontology.name] = '%x'
        for child in all_rules:
            items = child.find_overclaimed_item_for_provider("test", 0.5, rule_names_by_length, sequence_graphs, rule_frequencies, rule_ontologies)
        for child, other, frequency, expected in [
            (z, z_other_ontology, 0.9, ("", [(0, '3', 8)])),
            (x, x_super_duper_parent, 0.6, ("1", [(1, '2', 4), (1, '3', 8), (2, '4', 16)])),
            (x, x_parent_diff, 0.7, ("1_2 3", [(2, '4', 16)])),
            (x, x_parent_same, 0.8, ("1_2_4", [(1, '3', 8)])),
            (x, x_other_ontology, 0.9, ("1_2_4", [(1, '3', 8)])),
            (x, x_same_length_not_similar, 0.9, ("1_2_4", [(1, '3', 8)])),
            (x, x_same_length_similar, 0.9, ("1_1 3_4", [(1, '2', 2)])),
            (x, not_x_parent, 1, ("1_1 3_4", [(1, '2', 2)])),
            (y, y_same_length, 0.7, ("", [(0, '1', 2), (1, '2', 4), (1, '3', 8), (2, '4', 16), (3, '5', 32), (3, '6', 64)])),
            (z, z_other, 0.9, ("2", [(0, '3', 4)])),
        ]:
            rule_frequencies[other.name]["75"] = frequency
            items = child.find_overclaimed_item_for_provider("test", 0.5, rule_names_by_length, sequence_graphs, rule_frequencies, rule_ontologies)
            self.assertEqual(len(items), len(expected))
            self.assertEqual(len(items[1]), len(expected[1]))
            self.assertEqual(items[0], expected[0])

            for i, unusual in enumerate(items[1]):
                self.assertEqual(expected[1][i][0], unusual[0])
                self.assertEqual(expected[1][i][1], unusual[1])
                self.assertEqual(expected[1][i][2], unusual[2])
