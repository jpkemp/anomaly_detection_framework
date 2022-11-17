'''Classes for loading and using configuration information'''
# Apparently using un-classed variables for configuration is canonical in python.
# https://stackoverflow.com/questions/13034496/using-global-variables-between-files
# pylint: disable=W0603 ## using global intentionally here
from dataclasses import dataclass

# NOTE: these are updated in FileUtils.update_config, on test case load
DATA_PATH: str = ""
PARQUET: str = ""
PAT_ID: str = ""
DATE: str = ""
PR_ID: str = ""
PR_SP: str = ""
RPR_ID: str = ""
ITEM: str = ""
GL: str = ""
VALID: str = ""
COST: float = 0.0
HEADER: dict = None
DATE_FORMAT: str = ""

def convert_header(header: list):
    '''get configured field name from file field names'''
    ret = []
    config = test_config_loader()
    for key in header:
        if key in config.__dict__:
            ret.append(getattr(config, key))
        else:
            ret.append(key)

    return ret

def test_config_loader():
    '''load test config information'''
    ret = TestConfig()
    ret.PAT_ID = PAT_ID
    ret.DATE = DATE
    ret.PR_ID = PR_ID
    ret.PR_SP = PR_SP
    ret.RPR_ID = RPR_ID
    ret.ITEM = ITEM
    ret.GL = GL
    ret.VALID = VALID
    ret.COST = COST
    ret.HEADER = HEADER
    ret.DATE_FORMAT = DATE_FORMAT

    return ret

@dataclass
class TestConfig:
    '''Data attributes required for the analysis'''
    PAT_ID: str = ""
    DATE: str = ""
    PR_ID: str = ""
    PR_SP: str = ""
    RPR_ID: str = ""
    ITEM: str = ""
    GL: str = ""
    VALID: str = ""
    HEADER: dict = None
    DATE_FORMAT: str = ""

@dataclass
class FileConfig:
    '''File attributes required for loading source data'''
    DATA_PATH: str = ""
    PARQUET: str = ""
