'''Test cases for sequence mining'''
import unittest
from datetime import datetime as dt
import pandas as pd
from src.core.io.file_utils import FileUtils
FileUtils.update_config('./config.json')

from src.core.algorithms.sequence.format import FormatSpmf
from src.core.algorithms.sequence.sequence import SequentialPatternDetection as SPD
import src.core.io.config as hc

class SequenceCreationTest(unittest.TestCase):
    def setUp(self):
        test_items = ['1', '2', '4', '1', '3', '1', '2', '2', '2']
        test_dates = [dt(2021, 1, 2), dt(2021, 1, 3), dt(2021, 1, 3), dt(2021, 1, 5), dt(2021, 1, 4), dt(2021, 1, 8), dt(2021, 1, 9),
            dt(2021, 1, 17), dt(2021, 1, 25)]
        test_costs = [20, 30, 40, 20, 10, 20, 30, 30, 30]
        test_data = pd.DataFrame([test_items, test_dates, test_costs]).transpose()
        test_data.columns = [hc.ITEM, hc.DATE, hc.COST]
        self.test_data = test_data

    def test_sequence_construct(self):
        ret = FormatSpmf.construct_sequence(self.test_data, "testing")
        expected_sequence = ['1', '2 4', '3', '1', '1', '2', '2', '2'] # test that order is correct
        expected_costs = [20, 70, 10, 20, 20, 30, 30, 30]
        expected_timestamps = [1, 2, 3, 4, 7, 8, 16, 24]
        self.assertEqual(ret.identifier,"testing")
        for test, expected in [(ret.sequence, expected_sequence), (ret.costs, expected_costs), (ret.timestamps, expected_timestamps)]:
            for i, test_val in enumerate(test):
                self.assertEqual(test_val, expected[i])

    def test_spmf_standard(self):
        sequence = FormatSpmf.construct_sequence(self.test_data, "testing").sequence
        sequences = [sequence, sequence, sequence]
        expected = "@CONVERTED_FROM_TEXT\n@ITEM=0=1\n@ITEM=1=2\n@ITEM=2=3\n@ITEM=3=4\n"
        expected += '\n'.join(['0 -1 1 3 -1 2 -1 0 -1 0 -1 1 -1 1 -1 1 -1 -2'] * 3) + '\n'
        test = FormatSpmf.convert_to_spmf_standard(sequences)
        for i, test_val in enumerate(test):
            self.assertEqual(test_val, expected[i])

    def test_spmf_episode(self):
        construct = FormatSpmf.construct_sequence(self.test_data, "testing")
        sequence = construct.sequence
        date = construct.timestamps
        expected = '\n'.join(['1|1', '2 4|2', '3|3', '1|4', '1|7', '2|8', '2|16', '2|24'])
        test = FormatSpmf.convert_to_spmf_episode(sequence, date)
        for i, test_val in enumerate(test):
            self.assertEqual(test_val, expected[i])


    def test_mine_lpps(self):
        seq = FormatSpmf.construct_sequence(self.test_data, "testing")
        result = SPD.mine_local_periodic_patterns(seq.sequence, seq.timestamps, 3, 1, 0)
        expected_patterns = set('1')
        expected_timestamps = tuple([1,7])
        self.assertEqual(len(result[0]), 1)
        self.assertEqual(result[0][0], expected_patterns)
        self.assertEqual(len(result[1]), 1)
        self.assertEqual(result[1][0], expected_timestamps)
