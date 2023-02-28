from overrides import overrides
import pandas as pd
from src.core.base.base_data_extraction import DataExtractionBase
from src.core.base.abstract_analysis import AbstractAnalysisBase
from src.core.base.obtain_data_from_sample import ObtainDataFromSample
from src.core.data_extraction.procedure_extraction import ProcedureExtractor
from src.core.io import config as hc


class DataExtraction(DataExtractionBase):
    @overrides
    def extract_data(self, analysis: AbstractAnalysisBase):
        code = analysis.required_params.code_of_interest
        data_path = f"gaa_{code}.pqt"
        data = self.try_load_data(analysis, data_path)
        if data is not None:
            data[hc.ITEM] = data[hc.ITEM].astype(str)
            data[hc.COST] = data[hc.COST].astype(float)
            data[hc.DATE] = pd.to_datetime(data[hc.DATE], format=hc.DATE_FORMAT)
        else:
            sample_extractor = SampleData(analysis)
            data = sample_extractor.combine_10p_data(analysis.logger, analysis.required_params.years)
            data = sample_extractor.get_test_data(data)
            path = analysis.get_project_root() / 'data' / data_path
            data.to_parquet(path)

        return data

class SampleData(ObtainDataFromSample):
    def __init__(self, analysis):
        core_cols = [hc.ITEM, hc.PR_ID, hc.PAT_ID, hc.DATE, hc.COST, hc.PR_SP, hc.GL]
        self.FINAL_COLS =  core_cols + ["EventID", "EpisodeID"]
        self.INITIAL_COLS = core_cols + [hc.VALID]
        self.analysis = analysis
        self.extract = ProcedureExtractor(self.analysis.logger, self.analysis.code_converter)

    @overrides
    def process_dataframe(self, data) -> pd.DataFrame:
        self.analysis.log("Processing dataframe")
        code = self.analysis.required_params.code_of_interest
        data = self.extract.get_same_day_claims([code], data, False, True)
        data["EpisodeID"] = data["EventID"] + "**" + data[hc.PR_ID]

        return data

    @overrides
    def get_test_data(self, data):

        return data