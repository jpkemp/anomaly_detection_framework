import os
from datetime import datetime
from overrides import overrides
from src.core.base.abstract_data_extraction import AbstractDataExtraction
from src.core.base.base_analysis import AnalysisBase
from src.core.io.spark.spark_wrapper import SparkWrapper, MbsExtractTypes, PbsExtractTypes
from src.core.mbs_info.code_converter import CodeConverter# codes_file = 'ortho_codes.csv'
import src.core.io.config as hc

class DataExtraction(DataExtractionBase):
    @overrides
    def extract_data(self, analysis: AnalysisBase):
        path = f"full_ortho_plus.pqt"
        data = self.try_load_data(analysis, path)
        if data is None:
            codes_file = f'{os.path.expanduser("~")}/orthopluscodes.csv'
            min_date = datetime(2019, 10, 1)
            max_date = datetime(2020, 9, 30)
            event_type = MbsExtractTypes.PatientEvents

            spark = SparkWrapper()
            data = spark.save_mbs_provider_data(min_date, max_date, codes, path, event_type)

        data[hc.PR_ID] = data[hc.PR_ID].astype(str)
        data[hc.COST] = data[hc.COST].astype(float)
        data["Header"] = data[hc.ITEM].apply(lambda x: self.code_converter.convert_mbs_code_to_ontology_label(x))

        return data