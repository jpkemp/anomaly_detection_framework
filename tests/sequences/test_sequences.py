'''Test cases for sequence mining'''
import unittest
from src.core.algorithms.sequence.merger import Merger
from src.core.algorithms.sequence.sequence import SequentialPatternDetection as SPD

class SequenceMergeTest(unittest.TestCase):
    def setUp(self):
        self.test_patterns = [
                    ('A'),
                    ('B'),
                    ('C'),
                    ('X', 'Q'),
                    ('M'),
                    ('Y'),
                    ('Z')
        ]
        self.test_timestamps = [
            (1, 3),
            (2, 4),
            (4, 6),
            (15, 17),
            (9, 10),
            (18, 18),
            (19, 20)
        ]

    def test_overlapping_sequence_merge(self):
        for tolerance, expected_patterns, expected_timestamps in [
            (0, [tuple(['A', 'B', 'C']), tuple(['M']), tuple(['Q', 'X']), tuple('Y'), tuple('Z')], [(1, 6), (9, 10), (15, 17), (18, 18), (19, 20)]),
            (1, [tuple(['A', 'B', 'C']), tuple(['M']), tuple(['Q', 'X', 'Y', 'Z'])], [(1, 6), (9, 10), (15, 20)]),
            (2, [tuple(['A', 'B', 'C']), tuple(['M']), tuple(['Q', 'X', 'Y', 'Z'])], [(1, 6), (9, 10), (15, 20)]),
            (3, [tuple(['A', 'B', 'C', 'M']), tuple(['Q', 'X', 'Y', 'Z'])], [(1, 10), (15, 20)]),
            (4, [tuple(['A', 'B', 'C', 'M']), tuple(['Q', 'X', 'Y', 'Z'])], [(1, 10), (15, 20)]),
            (5, [tuple(['A', 'B', 'C', 'M', 'Q', 'X', 'Y', 'Z'])], [(1, 20)])
        ]:
            patterns, timestamps = SPD.combine_overlapping_timestamped_patterns(self.test_patterns, self.test_timestamps, tolerance=tolerance)
            self.assertEqual(len(patterns), len(expected_patterns))
            self.assertEqual(len(timestamps), len(expected_timestamps))
            for i, pat in enumerate(patterns):
                self.assertEqual(pat, expected_patterns[i])

            for i, stamp in enumerate(timestamps):
                self.assertEqual(stamp, expected_timestamps[i])

    def test_merge_initiators(self):
        initiator_dates = [3, 6, 7, 8, 9, 14, 16, 21]
        patterns, timestamps = SPD.combine_overlapping_timestamped_patterns(self.test_patterns, self.test_timestamps, tolerance=0)
        max_intervals = [0, 1, 2, 3, 4, 5, 6]
        no_drop_expecteds = [
            [(1, 6), (9, 10), (15, 17), (18, 18), (19, 20)],
            [(1, 6), (8, 10), (14, 17), (18, 18), (19, 20)],
            [(1, 6), (7, 10), (14, 18), (19, 20)],
            [(1, 10), (14, 20)],
            [(1, 10), (14, 20)],
            [(1, 10), (14, 20)], # note this stays at 14 instead of 9 because 14 is the initiator date and 15 is the sequence
            [(1, 20)],
        ]
        drop_expecteds = [
            [(1, 6), (9, 10), (15, 17)],
            [(1, 6), (8, 10), (14, 17)],
            [(1, 6), (7, 10), (14, 18)],
            [(1, 10), (14, 20)],
            [(1, 10), (14, 20)],
            [(1, 10), (14, 20)],
            [(1, 20)],
        ]

        for drop, expecteds in [(True, drop_expecteds), (False, no_drop_expecteds)]:
            for i, intvl in enumerate(max_intervals):
                test = Merger.merge_initiator(initiator_dates, timestamps, intvl, drop_no_initiator=drop)
                expected = expecteds[i]
                self.assertEqual(len(test), len(expected))
                for j, x in enumerate(test):
                    self.assertEqual(x, expected[j])