'''Template for data analyses'''
import re
from dataclasses import dataclass
from pathlib import Path
import pandas as pd
from overrides import overrides
from tqdm import tqdm
from src.core.algorithms.similarity import convert_series_to_tied_list, rbo_with_ties
from src.core.base.base_analysis import AnalysisBase
import src.core.io.config as hc

class Analysis(AnalysisBase):
    '''Data analysis base class'''
    @dataclass
    class RequiredParams:
        '''Parameters required for the analysis'''
        gaa_rank: str = ''
        lda_rank: str = ''
        gaa_comp: str = ''
        lda_comp: str = ''
        rbo_param: float = 0.99

    def get_rank(self, data):
        '''parse the results from file'''
        folder = self.get_project_root() / "Output" / data
        scores = pd.read_csv(f"{folder}/final_scores.csv",
                             dtype=str)
        if 'index' in scores.columns:
            scores.index = scores["index"]
        else:
            scores.index = scores["Unnamed: 0"]

        scores = scores["WeightedMedian"].astype(float)
        sorted_weighted_rank = scores.sort_values(ascending=False)

        return convert_series_to_tied_list(sorted_weighted_rank)

    @overrides
    def run_test(self) -> None:
        self.log("Running test")
        rp = self.required_params
        gaa = self.get_rank(rp.gaa_rank)
        lda = self.get_rank(rp.lda_rank)

        max_len = min(len(lda), len(gaa))
        top = rbo_with_ties(lda[:max_len], gaa[:max_len], rp.rbo_param)
        self.log(f"RBO in top 100: {top}")
        lda_len = len(lda)
        gaa_len = len(gaa)
        self.log(f"GAA providers: {gaa_len}")
        self.log(f"LDA providers: {lda_len}")
        working_len = min(lda_len, gaa_len)

        self.log("Getting non-handover provider data")
        non_handover_providers = []
        comparison_folders = [rp.gaa_comp, rp.lda_comp]
        for folder in comparison_folders:
            path = self.get_project_root() / f'Output/{folder}/unknown_providers.csv'
            providers = set(pd.read_csv(path, dtype=str)['0'].values.tolist())
            non_handover_providers.append(providers)

        overlap = set.intersection(*non_handover_providers)
        non_overlap = set.symmetric_difference(*non_handover_providers)
        self.log(f"Number of same non-handover providers: {len(overlap)}")
        self.log(f"Number of different non-handover providers: {len(non_overlap)}")
        for provider in tqdm(set.union(*non_handover_providers)):
            provider_data = self.test_data[self.test_data[hc.PR_ID] == provider]
            provider_data.to_csv(self.logger.get_file_path(f"provider_{provider}.csv"))

        providers_to_check = set.union(*non_handover_providers)
        self.pickle_data(providers_to_check, "providers_to_check")
