'''Template for data analyses'''
from dataclasses import dataclass
from functools import reduce
from glob import glob
from itertools import combinations
import numpy as np
import pandas as pd
import pingouin as pg
from math import isclose
from overrides import overrides
from tqdm import tqdm
from src.core.algorithms.similarity import convert_series_to_tied_list, average_overlap, rbo_with_ties
from src.core.base.base_analysis import AnalysisBase
import src.core.io.config as hc

class Analysis(AnalysisBase):
    '''Data analysis base class'''
    @dataclass
    class RequiredParams:
        '''Parameters required for the analysis'''
        output_name: str = ""
        test_hash: int = None
        rbo_param: float = 0.99
        tol: float = 10e3

    @overrides
    def run_test(self) -> None:
        self.log("Running test")
        rp = self.required_params
        data = self.test_data
        data[hc.COST] = data[hc.COST].astype(float)
        data["EpisodeID"] = data["EventID"] + "**" + data[hc.PR_ID]
        total_episode_costs = data.groupby("EpisodeID").agg({hc.COST: 'sum'})
        total_episode_costs.index = pd.Series(total_episode_costs.index).apply(lambda x: x.split('**')[1])
        total_episode_costs.reset_index(inplace=True)
        total_provider_costs = data.groupby(hc.PR_ID).agg({hc.COST: 'sum'})
        total_provider_costs.index.name = hc.PR_ID
        total_provider_costs = pd.Series(total_provider_costs[hc.COST])
        median = total_episode_costs.groupby('EpisodeID').agg({hc.COST: 'median'})
        median.index.name = hc.PR_ID
        median = pd.Series(median[hc.COST])
        median.index.name = 'index'
        n_episodes = data.groupby(hc.PR_ID).agg({"EpisodeID": pd.Series.nunique})
        n_episodes.index.name = hc.PR_ID
        n_episodes = pd.Series(n_episodes["EpisodeID"])
        n_episodes.index.name = 'index'
        weighted_median_cost = median * n_episodes

        folder = f"{str(self.get_project_root())}/Output/{self.required_params.output_name}*"
        subfolders = glob(folder)
        scores = []
        for f in tqdm(subfolders):
            fi = f"{f}/hash.pkl"
            h = self.unpickle_data(fi)
            if h == rp.test_hash:
                score_file = f"{f}/final_scores.csv"
                subheading_name = f"{f}/subheadings.pkl"
                try:
                    temp = pd.read_csv(score_file, dtype=str)
                    aasodh = self.unpickle_data(subheading_name)
                except FileNotFoundError:
                    self.log(f"No scores file found in folder {f}")
                    continue

                score = temp["WeightedMedian"].astype(float)
                score.index = temp["Unnamed: 0"]
                scores.append(score)

        all_scores = pd.concat(scores, axis=1).fillna(0)
        all_scores.columns = [f"test_{x}" for x in range(len(all_scores.columns))]
        all_scores.index.name = "index"
        path = self.logger.get_file_path('all_scores.pqt')
        all_scores.to_parquet(path)
        largest_diff = all_scores.apply(lambda x: x.max() - x.min(), axis=1)
        self.log(f"Largest provider change for provider {largest_diff.idxmax()}")
        self.log("Largest diff description")
        self.log(largest_diff.describe())
        percent_diff = largest_diff / total_provider_costs
        self.log("Percent diff description")
        self.log(percent_diff.describe())
        path = self.logger.get_file_path('diff.pqt')
        self.plots.create_boxplot(largest_diff, "Differences between provider scores", path)
        path = self.logger.get_file_path('pdiff.pqt')
        self.plots.create_boxplot(percent_diff, "Differences between provider percents", path)
        melt = pd.melt(all_scores.reset_index(), id_vars=["index"], value_vars=all_scores.columns)
        melt.value = melt.value.astype(float)
        path = self.logger.get_file_path('scores.pqt')
        melt.to_parquet(path)
        melt["log"] = melt['value'].apply(lambda x: np.log(x)).replace(- np.inf, 0)

        path = self.logger.get_file_path("icc.csv")
        pg.intraclass_corr(melt, targets='variable', raters='index', ratings='value').to_csv(path)
        path = self.logger.get_file_path("icc_log.csv")
        pg.intraclass_corr(melt, targets='variable', raters='index', ratings='log').to_csv(path)


        ranks = [convert_series_to_tied_list(x) for x in tqdm(scores)]
        # ranks = [x["WeightedMedian"].index.tolist() for x in tqdm(scores)]
        rbos = []
        for a, b in tqdm(combinations(ranks, 2)):
            len_a = len(a)
            len_b = len(b)
            size = min(len_a, len_b)
            if len_a != len_b:
                self.log("Unequal lists")

            rbos.append(rbo_with_ties(a[:size], b[:size], rp.rbo_param))
            # rbos.append(average_overlap(a[:size], b[:size]))

        rbos = pd.Series(rbos)
        self.log(rbos.describe())


        matrix = all_scores.values.tolist()
        idx = all_scores.index.tolist()
        def check_row_pairs(row):
            close = []
            for a, b in combinations(row, 2):
                close.append(isclose(a, b, abs_tol=rp.tol))

            return all(close)


        changed = []
        for i, x in enumerate(idx):
            if not check_row_pairs(matrix[i]):
                changed.append(x)

        n = len(all_scores) - len(changed)
        self.log(f"{n} unchanged of {len(all_scores)}")
        path = self.logger.get_file_path('change.csv')
        all_scores.loc[changed].to_csv(path)

        mean_of_weights = all_scores.mean(axis=1)
        mean_of_weights.name = "WeightedMedian"
        path = self.logger.get_file_path('final_scores.csv')
        mean_of_weights.to_csv(path)
