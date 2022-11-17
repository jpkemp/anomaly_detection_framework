'''abstract class for data analysis'''
from abc import ABC, abstractmethod
from pathlib import Path
import pandas as pd
from src.core.base.abstract_attributes import abstract_attribute, AbstractMeta

class AbstractAnalysisBase(ABC, metaclass=AbstractMeta):
    '''Mandatory function and attribute definitions for test cases'''
    @abstract_attribute
    class RequiredParams:
        '''Parameters required for the analysis'''

    @abstract_attribute
    def required_params(self):
        '''Stores required parameters'''

    @abstract_attribute
    def data(self) -> pd.DataFrame:
        '''Stores data'''

    @abstractmethod
    def log(self, text) -> None:
        '''Wrapper for quick logging and printing'''

    @abstractmethod
    def pickle_data(self, data: object, filename: str, save_to_data_folder: bool=False) -> None:
        '''Wrapper for pickling to file'''

    def unpickle_data(self, filename: str, check_data_folder: bool=True):
        '''Wrapper for unpickling file'''

    @classmethod
    @abstractmethod
    def get_project_root(cls) -> Path:
        """Returns project root folder."""

    @abstractmethod
    def extract_data_from_specification(self) -> None:
        '''Save required data from source to file'''

    @abstractmethod
    def run_test(self) -> None:
        '''Run the analysis'''
