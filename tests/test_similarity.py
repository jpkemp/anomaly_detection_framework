'''test similarity algorithms'''
import unittest
from math import isclose
from src.core.algorithms.similarity import average_overlap, rbo, rbo_with_ties, rbo_weight_at_depth

class TestSimilarity(unittest.TestCase):
    '''test similarity algorithms'''
    def test_ao(self):
        '''test average overlap'''
        ranking_1 = ["John", "Lisa", "Morgan"]
        ranking_2 = ["Lisa", "Morgan", "John"]
        expected_1_2 = 0.5
        self.assertEqual(expected_1_2, average_overlap(ranking_1, ranking_2))

        ranking_3 = ["John", "Lisa", "Morgan", "Tyler"]
        ranking_4 = ["Lisa", "Morgan", "John", "Harry"]
        expected_3_4 = 2.25 / 4
        self.assertEqual(expected_3_4, average_overlap(ranking_3, ranking_4))

    def test_rbo(self):
        '''test rank-biased overlap'''
        ranking_1 = ["John", "Harry", "Bob"]
        ranking_2 = ["John", "Lisa", "Morgan"]
        p_1 = 0
        expected_1_2_p_1 = 1
        self.assertEqual(expected_1_2_p_1, rbo(ranking_1, ranking_2, p_1))
        p_2 = 0.3
        expected_1_2_p_2 = 0.826
        self.assertEqual(expected_1_2_p_2, rbo(ranking_1, ranking_2, p_2))

    def test_rbo_with_ties(self):
        '''test rbo with ties'''
        ranking_1 = [["John"], ["Lisa", "Morgan"], [], ["Tyler"]]
        ranking_2 = [["Lisa", "Morgan"], [], ["John"], ["Harry"]]
        p_1 = 0.2
        expected_1_2_p_1 = 0.1648
        self.assertAlmostEqual(expected_1_2_p_1, rbo_with_ties(ranking_1, ranking_2, p_1), places=8)

    def test_rbo_weight(self):
        # note expected values are from the Webber paper
        self.assertTrue(isclose(0.86, rbo_weight_at_depth(0.9, 10), rel_tol=0.01))
        self.assertTrue(isclose(0.86, rbo_weight_at_depth(0.98, 50), rel_tol=0.01))
