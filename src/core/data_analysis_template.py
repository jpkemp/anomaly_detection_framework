'''Template for data analyses'''
from dataclasses import dataclass
import pandas as pd
from overrides import overrides
from src.core.base.base_analysis import AnalysisBase
import src.core.io.config as hc

class Analysis(AnalysisBase):
    '''Data analysis base class'''
    @dataclass
    class RequiredParams:
        '''Parameters required for the analysis'''

    @overrides
    def run_test(self) -> None:
        self.log("Running test")
