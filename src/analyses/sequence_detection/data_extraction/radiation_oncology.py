from datetime import datetime
from overrides import overrides
import pandas as pd
from src.core.base.base_data_extraction import DataExtractionBase
from src.core.base.abstract_analysis import AbstractAnalysisBase
from src.core.io.spark.spark_wrapper import SparkWrapper, MbsExtractTypes, PbsExtractTypes
from src.core.mbs_info.code_converter import CodeConverter
from src.core.io import config as hc

class DataExtraction(DataExtractionBase):
    @overrides
    def extract_data(self, analysis: AnalysisBase):
        path = f"patients_radiation_planning_data_test.pqt"
        data = self.try_load_data(analysis, path)
        if data is not None:
            cdv = analysis.code_converter
            codes = cdv.get_mbs_items_in_subgroup(3, 'T2', 5)
            min_date = datetime(analysis.start_year,1,1)
            max_date = datetime(analysis.end_year,12,31)
            event_type = MbsExtractTypes.AllPatient
            spark = SparkWrapper()
            data = spark.save_mbs_provider_data(min_date, max_date, codes, path, event_type)

        data[hc.ITEM] = data[hc.ITEM].astype(str)
        data[hc.COST] = data[hc.COST].astype(float)
        data[hc.DATE] = pd.to_datetime(data[hc.DATE], format=hc.DATE_FORMAT)

        return data
