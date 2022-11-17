from abc import ABC, abstractmethod
import pandas as pd
from src.core.base.abstract_attributes import abstract_attribute, AbstractMeta
from src.core.base.abstract_analysis import AbstractAnalysisBase

class AbstractDataExtraction(ABC, metaclass=AbstractMeta):
    @abstractmethod
    def try_load_data(self, analysis, data_file: str, in_data_folder: bool = True):
        '''load data from file'''

    @abstractmethod
    def extract_data(self, analysis: AbstractAnalysisBase):
        '''function for extracting data. passing the analysis in to access logger etc'''
