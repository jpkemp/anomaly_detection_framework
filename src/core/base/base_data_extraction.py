from os.path import isfile
from overrides import overrides
import pandas as pd
from src.core.base.abstract_data_extraction import AbstractDataExtraction

class DataExtractionBase(AbstractDataExtraction):
    @overrides
    def try_load_data(self, analysis, data_file: str, in_data_folder: bool = True):
        analysis.log(f"Loading data from {data_file}")
        file_extension = data_file[-4:]
        if in_data_folder:
            data_folder = analysis.get_project_root() / "data"
            data_file = data_folder / data_file

        if not isfile(data_file):
            return None

        if file_extension == ".csv":
            data = pd.read_csv(data_file)
        elif file_extension == ".pkl":
            with open(data_file, 'rb') as f:
                data = pickle.load(f)
        elif file_extension == ".pqt":
            data = pd.read_parquet(data_file)
        else:
            raise AttributeError(f"Data file {data_file} extension should be .csv or .pkl")

        return data
