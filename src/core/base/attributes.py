'''add utilities to AnalysisBase'''
import hashlib
import pandas as pd
from src.core.io.logger import LoggingStructure
from src.core.io.config import convert_header
from src.core.io.plots import PlotUtils
from src.core.algorithms.graphs.mbs_graphs import MbsGraphColouring
from src.core.mbs_info.code_converter import CodeConverter

class AnalysisBaseAttributes:
    '''add utilities to AnalysisBase'''
    def __init__(self, logger: LoggingStructure, details, years):
        def _hash(obj):
            '''return a hash key based on keys and values'''
            if obj.__dict__ is None:
                key = hashlib.md5('None'.encode('utf-8')).hexdigest()

                return int(key, 16)

            dump = str(obj.__dict__)
            key = hashlib.md5(dump.encode('utf-8')).hexdigest()

            return int(key, 16)

        self.test_hash = _hash(details)
        self.logger = logger
        self.code_converter = CodeConverter(years[-1])
        self.plots = PlotUtils(logger)
        self.test_details = details
        self.start_year = years[0]
        self.end_year = years[-1]
        self.data: pd.DataFrame = None
