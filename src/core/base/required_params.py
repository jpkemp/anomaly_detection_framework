'''Store test parameters'''
class ParamCombiner:
    '''Combines parameters from run_analysis and the defaults in the test case'''
    def __init__(self, d, rp):
        self.analysis_file_location = None
        self.data_extract_specification = None
        for k in d:
            assert isinstance(k, str)
            if k not in rp:
                raise KeyError(f'Invalid key {k} in params. Required keys are {rp.keys()}')

        for k, v in rp.items():
            assert isinstance(k, str)
            if k in d:
                v = d[k]

            setattr(self, k, v)
            self.__dict__[k] = v

    def __repr__(self):
        return f"RequiredParams({str(self.__dict__)})"
