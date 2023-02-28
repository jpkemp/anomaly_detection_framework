'''Regional EDA'''
from dataclasses import dataclass
import pandas as pd
from overrides import overrides
from tqdm import tqdm
from src.core.base.base_analysis import AnalysisBase
from src.core.io import config as hc

class Analysis(AnalysisBase):
    '''Regional EDA'''
    @dataclass
    class RequiredParams:
        '''test parameters'''
        graph_style: str = 'fdp'
        code_of_interest: str = '49318'
        provider_header: str = hc.PR_ID

    class StateInformation:
        '''Exploratory statistics for each state'''
        def __init__(self, state):
            self.state: str = state
            self.item_stats = []
            self.provider_stats = []
            self.patient_stats = []
            self.provider_episode_stats = []
            self.claims_per_decision_provider = []
            self.episodes_per_decision_provider = []

    def __init__(self, logger, params, year):
        core_cols = ["EventID", hc.ITEM, hc.GL, hc.PR_ID, hc.RPR_ID, hc.PR_SP, hc.DATE]
        self.FINAL_COLS = core_cols + ["NSPR"]
        self.INITIAL_COLS = core_cols + [hc.VALID]
        super().__init__(logger, params, year)

    def create_eda_boxplots(self, states):
        '''make boxplots from the gathered data for all states'''
        labels = ["Nation"] + \
            [self.code_converter.convert_state_num(x) for x in range(1, 6)]

        item_stats = [si.item_stats for si in states]
        provider_stats = [si.provider_stats for si in states]
        patient_stats = [si.patient_stats for si in states]
        provider_episode_stats = [si.provider_episode_stats for si in states]
        claims_per_decision_provider = [si.claims_per_decision_provider for si in states]
        episodes_per_decision_provider = [si.episodes_per_decision_provider for si in states]
        self.plots.create_boxplot_group(item_stats, labels, "Claims per item", "claims_items")
        self.plots.create_boxplot_group(provider_stats, labels, "Claims per provider", "claims_providers")
        self.plots.create_boxplot_group(patient_stats, labels, "Claims per episode", "claims_episodes")
        self.plots.create_boxplot_group(provider_episode_stats, labels, "Episodes per provider", "episodes_providers")
        self.plots.create_boxplot_group(claims_per_decision_provider, labels, "Claims per decision-making provider", "d_claims_providers")
        self.plots.create_boxplot_group(episodes_per_decision_provider, labels, "Episodes per decision-making provider", "d_episodes_providers")

    def get_exploratory_stats(self, data, region):
        '''EDA'''
        rp = self.required_params
        state_info = self.StateInformation(region)
        self.log(f"Descriptive stats for {region}")
        self.log(f"{len(data)} claims")
        self.log(f"{len(data[hc.ITEM].unique())} items claimed")
        self.log(f"{len(data[hc.PR_ID].unique())} providers")
        self.log(f"{len(data['EventID'].unique())} patients")
        no_providers_of_interest = len(data.loc[data[hc.ITEM] == rp.code_of_interest, hc.PR_ID].unique())
        self.log(f"{no_providers_of_interest} decision-making providers for {region}")

        provider_episodes = []
        for _, g in data.groupby(hc.PR_ID):
            episodes = len(g['EventID'].unique())
            provider_episodes.append(episodes)

        for (description, header, filename, collection) in [
                ("Claims per item", hc.ITEM, hc.ITEM, state_info.item_stats),
                ("Claims per provider", hc.PR_ID, "provider", state_info.provider_stats),
                ("Claims per episode", "EventID", "episode", state_info.patient_stats),
                ("Episodes per provider", "provider_episodes", "provider_episodes", state_info.provider_episode_stats)
        ]:
            top_file = self.logger.get_file_path(f'top_{filename}_{region}.csv')
            if header == "provider_episodes":
                top_selection = pd.Series(provider_episodes).value_counts()
            else:
                top_selection = data[header].value_counts()

            top_code_counts = top_selection.values.tolist()
            for x in top_code_counts:
                collection.append(x)

            self.log(f"{description} in {region}")
            self.log(f"{top_selection.describe()}")

            if description == hc.ITEM:
                top_codes = top_selection.index.tolist()
                self.code_converter.write_mbs_codes_to_csv(
                    top_codes, top_file, [top_code_counts], ["No of occurrences"])

        for _, claims in data.groupby(rp.provider_header):
            patients = claims['EventID'].unique()
            state_info.episodes_per_decision_provider.append(len(patients))
            state_info.claims_per_decision_provider.append(len(claims))

        df = pd.DataFrame(state_info.episodes_per_decision_provider)
        self.log(f"Episodes per surgical provider in {region}")
        self.log(df.describe())

        return state_info

    @overrides
    def run_test(self) -> None:
        self.log("Running test")
        state_statistics = []
        state_information = self.get_exploratory_stats(self.data, "nation")
        state_statistics.append(state_information)
        # data = self.test_tools.exclude_multiple_states(self.data).groupby(hc.GL)
        data = self.data.groupby(hc.GL)
        for state, state_data in tqdm(data):
            state_information = self.get_exploratory_stats(state_data, self.code_converter.convert_state_num(state))
            state_statistics.append(state_information)

        self.create_eda_boxplots(state_statistics)
