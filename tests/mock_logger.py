# pylint: disable=W0107,R0903 ## unnecessary pass and too few public methods
'''Mock logger for unittests'''
from pathlib import Path

class MockLogger():
    '''Mock logger for unittests'''
    output_path = Path('./Output/')
    test_name = 'Mock'

    def log(self, line, line_end=None):
        '''log to nowhere'''
        pass
