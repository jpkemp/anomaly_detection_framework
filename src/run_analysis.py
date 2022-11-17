'''Run tests from proposals'''
import operator # pylint: disable=W0611
from dataclasses import dataclass
from enum import Enum, auto
from importlib import import_module
from src.core.base.base_analysis import AnalysisBase, AnalysisDetails
from src.core.io.file_utils import FileUtils
from src.core.io.logger import Logger

@dataclass
class RequiredParams:
    '''Set up non-default test parameters from dictionary'''
    def __init__(self, d):
        for k, v in d.items():
            setattr(self, k, v)

class RunAnalysis:
    '''run a AnalysisBase test case'''
    def __init__(self, config_path: str):
        FileUtils.update_config(config_path)

    def set_name(self, analysis_details: AnalysisDetails, additional_folder_name_part: str):
        '''Construct the test name from test details'''
        data_source = analysis_details.data_extract_specification
        analysis_years = f"{analysis_details.years[0]}" if len(analysis_details.years) == 1 \
            else f"{analysis_details.years[0]}-{analysis_details.years[-1]}"
        analysis_name = f'src.analyses.{analysis_details.analysis_file_location}_{analysis_details.analysis_file_name}_{data_source}_{analysis_years}'
        if additional_folder_name_part is not None:
            analysis_name = f'{analysis_name}_{additional_folder_name_part}'

        return analysis_name

    def load_module(self, test_details, logger) -> AnalysisBase:
        test_file = import_module(f"src.analyses.{test_details.analysis_file_location}.{test_details.analysis_file_name}")
        analysis_class = getattr(test_file, "Analysis")
        analysis = analysis_class(logger, test_details, test_details.years)

        return analysis

    def start(self, analysis_details, additional_folder_name_part=None):
        '''Run an analysis'''
        years = analysis_details.years
        analysis_name = self.set_name(analysis_details, additional_folder_name_part)
        with Logger(analysis_name, '/mnt/c/data') as logger:
            analysis = self.load_module(analysis_details, logger)
            logger.log(analysis_details.notes)
            data = analysis.extract_data_from_specification()
            analysis.data = data
            analysis.run_test()
