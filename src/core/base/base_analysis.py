'''base class for data analysis'''
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
import pickle
import pandas as pd
from overrides import overrides
from src.core.base.abstract_data_extraction import AbstractDataExtraction
from src.core.base.abstract_analysis import AbstractAnalysisBase
from src.core.base.attributes import AnalysisBaseAttributes
from src.core.base.required_params import ParamCombiner
from src.core.io.file_utils import FileUtils

@dataclass
class AnalysisDetails:
    '''Holds details for the analysis to be run'''
    notes: str
    params: dict
    data_extract_specification: str
    analysis_file_name: str
    analysis_file_location: str
    years: list

class AnalysisBase(AbstractAnalysisBase, AnalysisBaseAttributes):
    '''Run an analysis through the framework'''
    def __init__(self, logger, details: AnalysisDetails, years):
        super().__init__(logger, details, years)
        params = details.params
        rp = self.RequiredParams().__dict__
        for k, v in details.__dict__.items():
            rp[k] = v

        if params is None:
            self.required_params = ParamCombiner({}, rp)
        elif isinstance(params, dict):
            param_class = ParamCombiner(params, rp)
            self.required_params = param_class
        else:
            raise AttributeError(f"params must be of type None or dict, not {type(params)}")

        self.log(f"Test details hash: {self.test_hash}")
        self.log(str(self.required_params))

    @overrides
    def extract_data_from_specification(self) -> None:
        rp = self.required_params
        spec_location = f"src.analyses.{rp.analysis_file_location}.data_extraction.{rp.data_extract_specification}"
        data_extract_file = import_module(spec_location)
        data_extract_class = getattr(data_extract_file, "DataExtraction")
        data = data_extract_class().extract_data(self)

        return data

    @overrides
    def log(self, text) -> None:
        if self.logger is None:
            print(text)
        else:
            self.logger.log(text)

    @overrides
    def pickle_data(self, data, filename, save_to_data_folder=False) -> None:
        filename = str(filename)
        if filename[-4:-1] != ".pkl":
            filename = filename + ".pkl"

        if save_to_data_folder:
            filename = self.get_project_root() / f'data/{filename}'
        elif self.logger is not None:
            filename = self.logger.get_file_path(filename)


        with open(filename, 'wb') as f:
            pickle.dump(data, f)

    @overrides
    def unpickle_data(self, filename, check_data_folder=True):
        filepath = None
        if check_data_folder:
            filepath = self.get_project_root() / f'data/{filename}'
            if not filepath.is_file():
                filepath = None

        if filepath is None:
            filepath = Path(filename)

        with open(filepath, 'rb') as f:
            data = pickle.load(f)

        return data

    @classmethod
    @overrides
    def get_project_root(cls) -> Path:
        return FileUtils.get_project_root()
