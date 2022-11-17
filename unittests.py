'''run unittests'''
import unittest
import tests

if __name__ == "__main__":
    loader = unittest.defaultTestLoader
    test_suite = loader.loadTestsFromModule(tests)
    test_runner = unittest.TextTestRunner()
    test_results = test_runner.run(test_suite)
    print(test_results.wasSuccessful())
