from abc import ABC, abstractmethod
import os
import pandas as pd
from src.core.base.abstract_attributes import abstract_attribute, AbstractMeta
from src.core.io import config as hc

class ObtainDataFromSample(metaclass=AbstractMeta):
    @abstract_attribute
    def INITIAL_COLS(self):
        pass

    @abstract_attribute
    def FINAL_COLS(self):
        pass

    @abstractmethod
    def process_dataframe(self, data: pd.DataFrame) -> pd.DataFrame:
        '''Get required data from the source'''

    @abstractmethod
    def get_test_data(self, data):
        '''Modify the combined, processed data before the test'''

    def combine_10p_data(self, logger, years):
        '''gets columnar parquet data from given list of years and returns a pd dataframe'''
        filenames = self.get_data_files(years)
        data = pd.DataFrame(columns=self.FINAL_COLS)
        for filename in filenames:
            if logger is not None:
                logger.log(f"Opening {filename}")

            all_data = pd.read_parquet(filename, columns=self.INITIAL_COLS)
            for x in self.INITIAL_COLS:
                all_data[x] = all_data[x].astype(hc.HEADER[x])

            processed_data = self.process_dataframe(all_data)

            assert len(self.FINAL_COLS) == len(processed_data.columns)
            for i, _ in enumerate(self.FINAL_COLS):
                assert self.FINAL_COLS[i] == processed_data.columns[i]

            data = data.append(processed_data)

        return data

    @classmethod
    def get_data_files(cls, years):
        '''returns a list of mbs files'''
        all_files = [hc.DATA_PATH / f for f in os.listdir(hc.DATA_PATH) if f.lower().endswith(hc.PARQUET)]
        if not all_files:
            raise RuntimeWarning(f"No parquet files found in {hc.DATA_PATH}")

        files = []
        for filename in all_files:
            for year in years:
                if year in str(filename):
                    files.append(filename)

        return sorted(files)
