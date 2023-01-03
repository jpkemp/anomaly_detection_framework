'''Template for data analyses'''
from dataclasses import dataclass
from functools import reduce
from statistics import median
import pandas as pd
from overrides import overrides
from scipy.stats import percentileofscore
from tqdm import tqdm
from src.core.algorithms.arules.mba_model import MbaModel
from src.core.base.base_analysis import AnalysisBase
from src.core.data_extraction.data_grouper import DataGrouper
from src.core.io import config as hc
from src.analyses.ontology_context_discovery.helper_classes.writer import Writer
from src.analyses.ontology_context_discovery.helper_classes.subheading import Subheading
from src.analyses.ontology_context_discovery import layer_models
from src.analyses.ontology_context_discovery.layer_models.base import NoModelError

class Analysis(AnalysisBase):
    '''Data analysis base class'''
    @dataclass
    class RequiredParams:
        '''Parameters required for the analysis'''
        filters: dict = None
        rank_method: str = "WeightedMedian"
        role_modeller: str = "LDA"
        primary_header_stems: tuple = ("3_T8_14", "3_T8_15")

    def __init__(self, logger, details, year):
        self.FINAL_COLS = []
        self.INITIAL_COLS = self.FINAL_COLS
        super().__init__(logger, details, year)
        role_modeller = self.required_params.role_modeller
        if role_modeller == "GAA":
            self.create_role_data = layer_models.gaa.GaaRoles.create_role_data
        elif role_modeller == "LDA":
            self.create_role_data = layer_models.lda.LdaRoles.create_role_data
        else:
            raise ValueError(f"No role modeller defined as {role_modeller}")

    @overrides
    def run_test(self) -> None:
        self.log("Running test")
        data = self.test_data
        rp = self.required_params
        self.pickle_data(self.test_hash, "hash")

        final_provider_scores = []
        if rp.role_modeller == "GAA":
            subheadings = Subheading.find_subheadings(data, True, rp.primary_header_stems)
        else:
            subheadings = Subheading.find_subheadings(data, False, rp.primary_header_stems)

        for label, s in tqdm(subheadings.items()):
            try:
                self.create_role_data(self, self.log, label, s)
            except NoModelError:
                self.log(f"No model created for subheading {label}")
                continue

            provider_scores = {}
            role_providers = {}
            for role in s.role_data:
                if not s.role_data[role].fees:
                    self.log(f"Role {role} has no episodes")
                    continue

                role_fee = s.role_data[role].calculate_expected_fee()
                self.log(f"Typical fee for subheading {label} role {role}: {role_fee}")
                role_providers[role] = list(set(x for i, x in enumerate(s.order) if s.roles[i] == role))
                provider_scores[role] = {}
                for prov in role_providers[role]:
                    provider_scores[role][prov] = []

            no_role = len(s.role_data) - 1
            number_of_no_roles = 0
            for i, ep in enumerate(s.episodes): # pylint:disable=unused-variable
                role = s.roles[i]
                prov = s.order[i]
                if role == no_role:
                    number_of_no_roles += 1
                    continue

                error = s.fees[i] - s.role_data[role].fee
                provider_scores[role][s.order[i]].append(error)

            for role in provider_scores:
                if role == no_role:
                    continue

                medians = []
                n = []
                for scores in provider_scores[role].values():
                    n_scores = len(scores)
                    medians.append(median(scores) if n_scores > 1 else scores[0])
                    n.append(n_scores)

                role_scores = pd.DataFrame([n, medians], index=["N", "Median"], columns=list(provider_scores[role].keys())).transpose()
                role_scores[rp.rank_method] = role_scores["N"] * role_scores["Median"]
                if role_scores.empty:
                    self.log(' '.join(f"No providers with at least {rp.filter_role_providers_with_less_than_x_episodes} \
                        in subheading {label} role {role}".split()))
                    continue

                providers_of_interest = role_scores[rp.rank_method].sort_values(ascending=False)
                path = self.logger.get_file_path(f"top_providers_subheading_{label}_role_{role}.csv")
                providers_of_interest.to_csv(path)
                providers_of_interest[providers_of_interest < 0] = 0
                final_provider_scores.append(providers_of_interest)

            self.log(f"No role episodes for {label}: {number_of_no_roles}")
            self.log(f"Total episodes for {label}: {len(s.order)}")

        self.pickle_data(subheadings, "subheadings")
        final_ranking = reduce(lambda x, y: x.add(y, fill_value=0), final_provider_scores).sort_values(ascending=False)
        final_ranking.columns = ["suspicion_score"]
        path = self.logger.get_file_path(f"final_scores.csv")
        final_ranking.to_csv(path)
