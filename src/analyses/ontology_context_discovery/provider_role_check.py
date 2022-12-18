'''Template for data analyses'''
from dataclasses import dataclass
from glob import glob
from statistics import median
import pandas as pd
from gensim import corpora
from overrides import overrides
from tqdm import tqdm
from src.core.base.base_analysis import AnalysisBase
import src.core.io.config as hc

class Analysis(AnalysisBase):
    '''Data analysis base class'''
    @dataclass
    class RequiredParams:
        '''Parameters required for the analysis'''
        provider_id: str = ""
        test_hash: int = None
        output_name: str = "src.subheading_role_costs_role_costs"

    @overrides
    def run_test(self) -> None:
        self.log("Running test")
        rp = self.required_params
        data = self.test_data

        folder = f"{str(self.get_project_root())}/Output/{self.required_params.output_name}*"
        subfolders = glob(folder)
        models = []
        for f in tqdm(subfolders):
            fi = f"{f}/hash.pkl"
            try:
                h = self.unpickle_data(fi)
            except FileNotFoundError:
                self.log(f"No hash file in {f}")
                continue

            if h == rp.test_hash:
                subheading_name = f"{f}/subheadings.pkl"
                try:
                    models.append(self.unpickle_data(subheading_name))
                except FileNotFoundError:
                    continue

        n_episodes = []
        subheading_roles = []
        costs = []
        for run, context in enumerate(tqdm(models)):
            episodes = 0
            roles = []
            sub_costs = []
            for label, subheading in context.items():
                corp_map = corpora.Dictionary(subheading.episodes)
                for i, prov in enumerate(subheading.order):
                    if prov == rp.provider_id:
                        episode = subheading.episodes[i]
                        episodes += 1
                        role_prediction = subheading.model[corp_map.doc2bow(episode)]
                        roles.append(f"{label}_{subheading.roles[i]}")
                        sub_costs.append(subheading.fees[i])

            subheading_roles.append(roles)
            n_episodes.append(episodes)
            costs.append(sub_costs)

        for i, x in enumerate(tqdm(subheading_roles)):
            counts = pd.Series(x).value_counts()
            self.log(f"Test {i} role counts")
            self.log(counts)
            highest = counts.idxmax()
            head = highest[:-2]
            role = int(highest[-1])
            subheading = models[i][head]
            self.log(f"{len(subheading.episodes)} subheading episodes")
            self.log(f"{len(subheading.role_data[role].fees)} role episodes")
            self.log(f"{subheading.role_data[role].fee} role cost")
            provider_costs = [q for j, q in enumerate(costs[i]) if subheading_roles[i][j] == highest]
            current = median(provider_costs)
            self.log(f"{current} median provider role cost")
            model = subheading.model
            self.log(model.print_topic(role))

        self.log("n_episodes")
        self.log(n_episodes)



