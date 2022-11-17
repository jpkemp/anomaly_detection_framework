from unittest import TestSuite
from tests.test_code_converter import TestCodeConverter
from tests.test_similarity import TestSimilarity
from tests.sequences.test_containers.test_courses import SequenceFlagTest
from tests.sequences.test_containers.test_patients import SequenceContainersTest
from tests.sequences.test_containers.test_sequence_graphs import TestSequenceGraph
from tests.sequences.test_sequence_format import SequenceCreationTest
from tests.sequences.test_sequences import SequenceMergeTest

def load_tests(loader, standard_tests, pattern):
    test_cases = (TestCodeConverter,
                  TestSimilarity,
                  SequenceFlagTest,
                  SequenceContainersTest,
                  TestSequenceGraph,
                  SequenceCreationTest,
                  SequenceMergeTest)
    suite = TestSuite()
    for test_class in test_cases:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    return suite