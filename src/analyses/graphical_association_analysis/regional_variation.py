'''Finds variations between regional AA models'''
from dataclasses import dataclass
import pandas as pd
from tqdm import tqdm
from overrides import overrides
from src.core.algorithms.arules.mba_model import MbaModel
from src.core.data_extraction.data_grouper import DataGrouper
from src.core.base.base_analysis import AnalysisBase
from src.core.io import config as hc

class Analysis(AnalysisBase):
    '''Regional MBA'''
    @dataclass
    class RequiredParams:
        '''test parameters'''
        colour_only: bool = True
        min_support: float = 0.05
        filters: dict = None
        graph_style: str = 'fdp'
        code_of_interest: str = '49318'
        provider_header: str = hc.PR_ID

    def __init__(self, logger, params, year):
        core_cols = ["EventID", hc.ITEM, hc.GL, hc.PR_ID, hc.RPR_ID, hc.PR_SP, hc.DATE]
        self.FINAL_COLS = core_cols + ["NSPR"]
        self.INITIAL_COLS = core_cols + [hc.VALID]
        super().__init__(logger, params, year)

    def get_state_sets(self, state_records):
        '''gets items in each state'''
        state_sets = []
        for state in state_records:
            s = self.graphs.flatten_graph_dict(state)
            state_sets.append(s)

        return state_sets

    def get_state_costs(self, state_sets, state_order):
        '''get the cost of items in each state'''
        supp = self.required_params.min_support
        for i, state in enumerate(state_sets):
            total_cost = 0
            name = f"costs_for_state_{self.code_converter.convert_state_num(state_order[i])}_supp_{supp}.csv"
            filename = self.logger.get_file_path(name)
            with open(filename, 'w+') as f:
                f.write(
                    "Group,Category,Sub-Category,Item,Description,Cost,FeeType\r\n")
                for item in state:
                    code = item.split('\n')[-1]
                    line = ','.join(self.code_converter.get_mbs_code_as_line(code))
                    item_cost, fee_type = self.code_converter.get_mbs_item_fee(code)
                    total_cost += item_cost
                    item_cost = "${:.2f}".format(item_cost)
                    f.write(f"{line},{item_cost},{fee_type}\r\n")

                total_cost_str = "${:.2f}".format(total_cost)
                self.log(f"Cost for {self.code_converter.convert_state_num(state_order[i])}: {total_cost_str}")

    def get_differences(self, state_sets):
        '''get item differences between states and write to file'''
        differences = set()
        for i in state_sets:
            for j in state_sets:
                differences.update(i.difference(j))

        differences = list(differences)
        states = []
        for item in differences:
            item_states = []
            for i, state in enumerate(state_sets):
                if item in state:
                    item_states.append(i)

            item_states = '; '.join(
                [self.code_converter.convert_state_num(x+1) for x in item_states])
            states.append(item_states)

        supp = self.required_params.min_support
        diff_file = self.logger.get_file_path(f'diff_file_supp_{supp}.csv')
        self.code_converter.write_mbs_codes_to_csv(differences,
                                                             diff_file,
                                                             additional_headers=['States'],
                                                             additional_cols=[states])

        return differences

    def get_similarities(self, state_sets):
        '''get item similarities between states and write to file'''
        sames = set.intersection(*state_sets)
        supp = self.required_params.min_support
        same_file = self.logger.get_file_path(f'same_file_supp_{supp}.csv')
        self.code_converter.write_mbs_codes_to_csv(sames, same_file)

        return sames

    @overrides
    def run_test(self) -> None:
        self.log("Running test")
        rp = self.required_params
        state_records = []
        state_order = []
        node_labels = [
            (str(rp.code_of_interest), "Surgeon"),
            ("21214", "Anaesthetist"),
            ("21638", "Anaesthetist"),
            ("21402", "Anaesthetist"),
            ("51303", "Assistant"),
            ("105", "Consultant")
        ]

        for state, data in tqdm(self.data.groupby(hc.GL)):
            state_order.append(state)
            all_unique_items = [str(x) for x in data[hc.ITEM].unique().tolist()]
            mba = MbaModel(self.logger, self.code_converter, rp.filters)
            grouped_data = DataGrouper(self.logger, data, hc.ITEM, "EventID", rp.provider_header)
            documents = grouped_data.create_documents()
            d, labeller = mba.create_reference_model(rp.min_support, state, documents, all_unique_items, node_labels)
            state_records.append(d)

        state_sets = self.get_state_sets(state_records)
        self.get_state_costs(state_sets, state_order)
        sames = self.get_similarities(state_sets)
        diffs = self.get_differences(state_sets)

        self.log("Similarities")
        sames_df = pd.Series([self.code_converter.get_mbs_item_fee(x)[0] for x in sames])
        self.pickle_data(sames_df, f"sames_{rp.code_of_interest}_{rp.min_support}", True)
        self.log(sames_df.describe())
        self.log("Differences")
        diff_df = pd.Series([self.code_converter.get_mbs_item_fee(x)[0] for x in diffs])
        self.pickle_data(diff_df, f"diffs_{rp.code_of_interest}_{rp.min_support}", True)
        self.log(diff_df.describe())
