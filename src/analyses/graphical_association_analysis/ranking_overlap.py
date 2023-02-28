'''Check rank differences'''
from dataclasses import dataclass
import pickle
import pandas as pd
from overrides import overrides
from src.core.algorithms.similarity import rbo_with_ties
from src.core.base.base_analysis import AnalysisBase

class Analysis(AnalysisBase):
    '''Data analysis base class'''
    @dataclass
    class RequiredParams:
        '''Parameters required for the analysis'''
        rank_weighting: float = 0.9
        code_of_interest: str = "49318"

    def __init__(self, logger, params, year):
        self.FINAL_COLS = []
        self.INITIAL_COLS = self.FINAL_COLS
        super().__init__(logger, params, year)

    @overrides
    def run_test(self) -> None:
        self.log("Running test")
        data_folder = self.get_project_root() / "data"
        files = list(data_folder.glob(f"suspicion_matrix_{self.required_params.code_of_interest}*"))
        self.log(f"{len(files)} files examined")
        rankings = []
        order = []
        scores = []
        for f in files:
            with open(f, 'rb') as g:
                df = pickle.load(g)
                order.append(f.name)
                providers= []
                scores.append(df["count"].values.tolist())
                current_score = df["count"].values.tolist()[0]
                current_providers = []
                # create rankings with ties as list of lists; see rbo_with_ties unit test
                for count, prov in df.values.tolist():
                    if count != current_score:
                        providers.append(current_providers)
                        for _ in range(len(current_providers) - 1):
                            providers.append([])

                        current_providers = []
                        current_score = count

                    current_providers.append(prov)

                providers.append(current_providers)
                for _ in range(len(current_providers) - 1):
                    providers.append([])

                assert len(providers) == len(df)
                rankings.append(providers)

        descriptions = []
        sensitivities = []
        for i, S in enumerate(rankings):
            descriptions.append(pd.Series(scores[i]).describe())
            sensitivities.append(order[i][-8:-4])
            for j, T in enumerate(rankings):
                similarity = rbo_with_ties(S, T, self.required_params.rank_weighting)
                self.log(f"RBO between {order[i]} and {order[j]}: {similarity}")

        sensitivities, descriptions = zip(*sorted(zip(sensitivities, descriptions)))
        df = pd.DataFrame(descriptions).transpose()
        df.columns = sensitivities

        path = self.logger.get_file_path("costs.csv")
        df.to_csv(path)
