'''File and logging classes and functions'''
import pickle
import json
from pathlib import Path
from pydoc import locate
import src.core.io.config as hc

class FileUtils:
    '''I/O functions'''
    @classmethod
    def update_config(cls, path):
        '''update config with values from file'''
        with open(path, 'r') as f:
            config = json.load(f)
            hc.DATA_PATH = Path(config["SOURCE_DATA_PATH"])
            hc.PARQUET = config["PARQUET_FILE_EXTENSION"]
            hc.PAT_ID = config["PATIENT_ID"]
            hc.DATE = config["DATE"]
            hc.PR_ID = config["PROVIDER_ID"]
            hc.PR_SP = config["PROVIDER_SPECIALTY"]
            hc.RPR_ID = config["REFERRING_PROVIDER"]
            hc.ITEM = config["ITEM"]
            hc.GL = config["GEOLOCATION"]
            hc.COST = config["COST"]
            hc.VALID = config["VALID_CLAIM"]
            hc.HEADER = {x: locate(y) for x, y in config["HEADER_DTYPE_MAP"].items()}
            hc.DATE_FORMAT = config["DATE_FORMAT"]

    @classmethod
    def get_project_root(cls) -> Path:
        """Returns project root folder."""
        return Path(__file__).parent.parent.parent.parent

    @classmethod
    def load_pickle(cls, file, in_data_folder=False):
        '''helper function for loading pickled data'''
        if in_data_folder:
            path = cls.get_project_root() / f"data/{file}"
        else:
            path = Path(file)

        with open(path, 'rb') as f:
            data = pickle.load(f)

        return data

    @classmethod
    def write_model_to_file(cls, code_converter, d, filename):
        '''Save a graph model'''
        header = "Item is commonly claimed during unliateral joint replacements in the state " \
                + "on the surgery date of service\n"
        with open(filename, 'w+') as f:
            f.write(header)
            subheader = "Category,Group,Sub-group,Item,Description\n"
            f.write(f'{subheader}')
            for node in d:
                line = code_converter.get_mbs_code_as_line(node)
                line = ','.join(line)
                f.write(f"{line}\n")
