'''Template for data analyses'''
import pickle
import re
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
import numpy as np
import pandas as pd
from overrides import overrides
from src.core.algorithms.similarity import convert_series_to_tied_list, rbo_with_ties
from src.core.base.base_analysis import AnalysisBase
import src.core.io.config as hc

class Analysis(AnalysisBase):
    '''Data analysis base class'''
    @dataclass
    class RequiredParams:
        '''Parameters required for the analysis'''
        # score_data: str = '' # GAA
        score_data: str = '' # LDA
        known_anomalous_providers: str = ""
        get_top_x_not_handover: int = 20

    @overrides
    def run_test(self) -> None:
        self.log("Running test")
        rp = self.required_params
        handover = self.unpickle_data(rp.known_anomalous_providers)

        folder = self.get_project_root() / "Output" / rp.score_data
        scores = pd.read_csv(f"{folder}/final_scores.csv",
                             dtype=str)
        # scores.index = scores["Unnamed: 0"]
        scores.index = scores["index"]
        scores = scores["WeightedMedian"].astype(float)
        self.log("Checking positive-value sum of scores")
        sorted_weighted_rank = scores.sort_values(ascending=False).index.tolist()
        top_100 = set(sorted_weighted_rank[:100])
        found = handover.intersection(top_100)
        self.log(f"Top 100 overlap with the anomalous set: {len(found)}")

        self.log("Checking high-scoring non-anomalous set providers")
        not_chris = top_100 - handover
        non_handover_of_interest = []
        for x in not_chris:
            idx = sorted_weighted_rank.index(x)
            non_handover_of_interest.append((idx, x))

        sorted_non_handover_of_interest = sorted(non_handover_of_interest, key=lambda x: x[0])
        extract_indices = [y[0] for y in sorted_non_handover_of_interest][:rp.get_top_x_not_handover]
        extract_non_handover = [y[1] for y in sorted_non_handover_of_interest][:rp.get_top_x_not_handover]
        pd.Series(extract_non_handover, index=extract_indices).to_csv(self.logger.get_file_path("unknown_providers.csv"))

        self.log("Checking anomalous set provider episode costs")
        median_episode_costs = {}
        n_episodes = {}
        provs = self.test_data.groupby(hc.PR_ID)
        for prov in handover:
            check = provs.get_group(prov)
            episodes = check.groupby("EventID")
            episode_cost = episodes.agg({hc.COST: 'sum'})[hc.COST].median()
            n = len(episodes)
            median_episode_costs[prov] = episode_cost
            n_episodes[prov] = n

        self.log("Checking interval list overlap")
        total_providers = len(sorted_weighted_rank)
        def even_intervals(x):
            return (x + 1) * int(total_providers / 100)

        def log_intervals(x):
            pass

        for interval_label, interval_calculation in [("evenly distributed", even_intervals)]:
            axis_labels = ("Top x providers from model ranking", "No. of matching anomalous set providers")
            for weight, rank in [("sum", sorted_weighted_rank)]:
                overlap = []
                intervals = []
                costs = []
                n_episode_means = []
                for x in range(100):
                    current_interval = interval_calculation(x)
                    if current_interval > total_providers:
                        current_interval = total_providers

                    intervals.append(current_interval)
                    test = set(rank[:current_interval])
                    matches = test.intersection(handover)
                    match_len = len(matches)
                    interval_cost = mean(median_episode_costs[x] for x in matches)
                    n = mean(n_episodes[x] for x in matches)
                    n_episode_means.append(n)
                    overlap.append(match_len)
                    costs.append(interval_cost)

                def transform_points(l):
                    max_l = max(l)
                    min_l = min(l)
                    norm = [(z - min_l) / (max_l - min_l) for z in l]
                    scaled = [(x * 160) + 20 for x in norm]

                    return scaled

                point_size = transform_points(n_episode_means)
                self.plots.create_scatter_plot_with_colourbar(intervals,
                                                overlap,
                                                costs,
                                                f"Overlap of anomalous set to {weight} list at {interval_label} intervals",
                                                f"overlap_{weight}_{interval_label}",
                                                axis_labels=axis_labels,
                                                cbar_label="Mean of median cost of anomalous set provider episodes ($)",
                                                marker_size=point_size,
                                                legend_title="Mean episodes\nper anomalous set provider",
                                                invert_x=True)
