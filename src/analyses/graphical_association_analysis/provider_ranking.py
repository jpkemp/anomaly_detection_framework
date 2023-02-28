'''Reference and provider model comparison and ranking'''
from dataclasses import dataclass
from enum import Enum
from itertools import combinations
import pandas as pd
import xlsxwriter
from overrides import overrides
from scipy.stats import percentileofscore
from tqdm import tqdm
from src.core.algorithms.arules.mba_model import MbaModel
from src.core.base.base_analysis import AnalysisBase
from src.core.data_extraction.data_grouper import DataGrouper
from src.core.io import config as hc

class Save(Enum):
    '''where to draw results from'''
    SAVE_X = 0
    SAVE_X_FROM_EACH = 1
    SAVE_X_FROM_COMPONENT_OF_INTEREST = 2

class Analysis(AnalysisBase):
    '''Data analysis base class'''
    @dataclass
    class RequiredParams:
        '''test parameters'''
        # code_of_interest: str = "49318"
        code_of_interest: str = "48918"
        min_support: float = 0.06
        provider_min_support: float = 0.5
        filters: dict = None
        exclude_providers_with_less_than_x_episodes: int = 3
        no_to_save: int = 10
        save_from: Save = Save.SAVE_X_FROM_COMPONENT_OF_INTEREST
        provider_header: str = hc.PR_ID

    @dataclass
    class ProviderMbaInfo:
        '''Store results for a provider from MBA and suspicion score'''
        provider_id: str = None
        suspicious_transactions_score: int = 0
        missing_expected_transactions_score: int = 0
        model_graph: dict = None
        model_attrs: dict = None
        edit_graph: dict = None
        edit_attrs: dict = None
        typical_provider_items: list = None
        provider_label: str = "Unassigned"
        closest_component: int = None
        rank: int = -1
        item_counts: pd.DataFrame = None


    def __init__(self, logger, params, year):
        nspr = ["NSPR"]
        core_cols = [hc.PAT_ID, hc.ITEM, hc.DATE, hc.PR_SP, hc.PR_ID]
        other_cols = [hc.VALID]
        self.FINAL_COLS = core_cols + nspr
        self.INITIAL_COLS = core_cols + other_cols
        super().__init__(logger, params, year)
        self.fee_record: dict = None
        self.mba = None

    def write_suspicions_to_file(self, attrs, open_xlsx, provider_results, component_item_occurences):
        '''Save a suspicious model to csv'''
        too_much = []
        too_little = []
        ok = []
        for node in attrs:
            try:
                shape = attrs[node]['shape']
            except KeyError:
                shape = 'ok'

            if shape in ('database', 'house'):
                too_much.append(node)
            elif shape in ('box', 'invhouse'):
                too_little.append(node)
            else:
                ok.append(node)

        f = open_xlsx.add_worksheet(f'Rank {provider_results.rank + 1} {provider_results.provider_label}')
        ital = open_xlsx.add_format({'italic': True})
        bold = open_xlsx.add_format({'bold': True})
        f.write('A1', 'Provider ID: ', ital)
        f.write('B1', provider_results.provider_id)
        row = 1
        for (section, header) in [(too_much,
                                    'Items in the provider model but not in the reference model\n'),
                                    (too_little,
                                    "\nExpected items in the model which do not commonly "\
                                        + "appear in the provider model\n"),
                                    (ok, "\nItems expected in the reference model that are in the provider model\n")]:
            f.write(row, 0, header, bold)
            row += 1
            subheader = ["Category","Group","Sub-group","Item","Description"]
            for i, x in enumerate(subheader):
                f.write(row, i, x, ital)

            row += 1
            for node in section:
                line_list = self.code_converter.get_mbs_code_as_line(node)
                for i, l in enumerate(line_list):
                    f.write(row, i, l)

                row += 1

            row += 1

        items = self.graphs.flatten_graph_dict(provider_results.model_graph)
        def get_percentiles(item, item_2, provider_results):
            oc_val = []
            for l in component_item_occurences[provider_results.closest_component]:
                try:
                    oc_val.append(l.at[item, item_2])
                except KeyError:
                    oc_val.append(0)

            s = pd.Series(oc_val)
            val = provider_results.item_counts.at[item, item_2]
            p = percentileofscore(s, val, kind='weak')
            q10 = s.quantile(0.1)
            q25 = s.quantile(0.25)
            q50 = s.quantile(0.50)
            q75 = s.quantile(0.75)
            q90 = s.quantile(0.90)
            n_claiming = len(s[s > 0])

            return (val, p, n_claiming), (q10, q25, q50, q75, q90)

        row += 1
        f.write(row, 0, "Claim occurence information", bold)
        row += 1
        next_header = ['Item','Provider claims','Provider percentile', 'Total providers with claim', "", "Q10", "Q25", "Median", "Q75", "Q90"]
        for i, x in enumerate(next_header):
            f.write(row, i, x, ital)

        for item in items:
            row += 1
            main_vals, quantiles = get_percentiles(item, item, provider_results)
            for i, x in enumerate([item] + list(main_vals) + [""] + list(quantiles)):
                f.write(row, i, x)

        for i, i2 in combinations(items, 2):
            row += 1
            main_vals, quantiles = list(get_percentiles(i, i2, provider_results))
            for i, x in enumerate([f"{i} {i2}"] + list(main_vals) + [""] + list(quantiles)):
                f.write(row, i, x)

    def save_graphs_to_images(self, provider_results):
        '''Format graph titles and save graphs to file for a given provider'''
        def save_standard_model():
            group_graph_title = f'Rank {provider_results.rank} {provider_results.provider_label} ' \
                                + 'normal basket ITEM for patients treated by with score ' \
                                + f'{provider_results.suspicious_transactions_score}'
            group_graph_name = f"_rank_{provider_results.rank}_{provider_results.provider_label}_normal_items"
            group_graph, group_attrs, _ = self.graphs.convert_mbs_codes(provider_results.model_graph, provider_results.model_attrs)
            self.mba.create_graph(group_graph,
                                group_graph_name,
                                # group_graph_title,
                                "",
                                attrs=group_attrs,
                                graph_style='fdp',
                                file_extension='svg')
            # self.graphs.create_visnetwork(
            #     group_graph, group_graph_name, group_graph_title, attrs=group_attrs)

        def save_edit_model():
            edit_graph_title = f'Rank {provider_results.rank} {provider_results.provider_label} ' \
                                + 'edit history of basket ITEM for patients treated by with score ' \
                                + f'{provider_results.suspicious_transactions_score:.2f}'
            edit_graph_name = f"_rank_{provider_results.rank}_{provider_results.provider_label}_edit_history_for_basket"
            _, new_edit_attrs, _ = self.graphs.colour_mbs_codes(provider_results.edit_graph)

            # format attributes to deal with multi-part node text
            for key in new_edit_attrs:
                code = key.split('\n')[-1]
                if provider_results.edit_attrs is not None:
                    if code in provider_results.edit_attrs:
                        new_edit_attrs[key] = {**provider_results.edit_attrs[code], **new_edit_attrs[key]}

            # self.mba.create_graph(provider_results.edit_graph, edit_graph_name, edit_graph_title, new_edit_attrs, 'fdp', 'svg')
            self.mba.create_graph(provider_results.edit_graph, edit_graph_name, None, new_edit_attrs, 'fdp', 'svg')
            # self.graphs.create_visnetwork(provider_results.edit_graph, edit_graph_name, edit_graph_title, attrs=new_edit_attrs)

            return new_edit_attrs

        save_standard_model()
        attrs = save_edit_model()

        return attrs

    def assign_node_style(self, provider_id, model, data, attrs=None):
        '''assign a node outline to indicate the beneficiary of the claim (referring provider or not)'''
        if attrs is None:
            attrs = {}

        items = self.graphs.flatten_graph_dict(model)
        item_info = data.groupby(hc.ITEM)
        for item in items:
            options = attrs.get(str(item), {'shape': 'circle'})
            if options['shape'] == 'invhouse':
                options["style"] = "dashed"
                attrs[str(item)] = options
                continue

            try:
                int(item)
            except ValueError:
                continue # can't get 'No other items' group

            beneficiaries = item_info.get_group(item)[self.required_params.provider_header]
            if all(beneficiaries == provider_id):
                options["style"] = "filled"
                attrs[str(item)] = options
            elif any(beneficiaries == provider_id):
                options["style"] = "dotted"
                attrs[str(item)] = options
            else:
                options["style"] = "dashed"
                attrs[str(item)] = options

        return attrs

    def process_provider_data(self, typical_model, provider_id, provider_model, provider_data, counts):
        '''create provider models and get scores'''
        info = self.ProviderMbaInfo()
        info.provider_id = provider_id
        (plus_ged, minus_ged), edit_d, edit_attr = self.graphs.graph_edit_distance(
            typical_model, provider_model, self.fee_record)
        info.suspicious_transactions_score = plus_ged
        info.missing_expected_transactions_score = minus_ged
        info.edit_attrs = self.assign_node_style(provider_id, edit_d, provider_data, edit_attr)
        info.edit_graph = edit_d
        info.model_graph = provider_model
        info.model_attrs = self.assign_node_style(provider_id, provider_model, provider_data)
        info.typical_provider_items = self.graphs.flatten_graph_dict(provider_model)
        info.item_counts = counts

        return info

    @overrides
    def run_test(self) -> None:
        self.log("Running test")
        rp = self.required_params
        data = self.data

        self.mba = MbaModel(self.logger, self.code_converter, rp.filters)
        all_unique_items = [str(x) for x in data[hc.ITEM].unique().tolist()]
        grouped_data = DataGrouper(self.logger, data, hc.ITEM, hc.PAT_ID, rp.provider_header)
        documents = grouped_data.create_documents()
        node_labels = [
            (str(rp.code_of_interest), "Surgeon"),
            ("21214", "Anaesthetist"),
            ("21638", "Anaesthetist"),
            ("21402", "Anaesthetist"),
            ("51303", "Assistant"),
            ("105", "Consultant")
        ]
        gl_typical_model, labeller = self.mba.create_reference_model(
            rp.min_support, "Australia", documents, all_unique_items, node_labels)
        component_of_interest = [i for i, x in enumerate(labeller.components) if str(rp.code_of_interest) in x]
        assert len(component_of_interest) == 1
        component_of_interest = component_of_interest[0]

        # get item fees for use as node weights
        self.fee_record = {x: {} for x in all_unique_items}
        for node in self.fee_record:
            fee = self.code_converter.get_mbs_item_fee(node)
            if fee[1] == "Not in dictionary":
                self.log(f"{node} not in dictionary")

            self.fee_record[node]['weight'] = fee[0]

        self.log("Creating provider models and suspicion scores")
        ranked_provider_info = {}
        sus_items = {}

        provider_data = data.groupby(rp.provider_header)
        for provider, group in tqdm(provider_data):
            provider_data_group = DataGrouper(None, group, hc.ITEM, hc.PAT_ID, hc.DATE)
            provider_docs = provider_data_group.create_documents()
            if len(provider_docs) < rp.exclude_providers_with_less_than_x_episodes:
                continue

            all_provider_items = list({item for doc in provider_docs for item in doc})
            provider_model, counts = self.mba.create_model(all_provider_items,
                                              provider_docs,
                                              min_support=rp.provider_min_support,
                                              min_support_count=0)
            info = self.process_provider_data(gl_typical_model, provider, provider_model, group, counts)
            labeller.label_provider(info)
            ranked_provider_info[provider] = info
            for prov_item in info.typical_provider_items:
                sus_item_count = sus_items.get(prov_item, 0) + 1
                sus_items[prov_item] = sus_item_count

        self.log("Finding item cooccurences by component")
        component_item_occurences = []
        for component in tqdm(range(len(labeller.components))):
            counts = [x.item_counts for x in ranked_provider_info.values() if x.closest_component == component]
            component_item_occurences.append(counts)

        self.log("Finding suspicious providers")
        def save_ranked_results(d, fname):
            suspicion_matrix = pd.DataFrame.from_dict(d, orient='index', columns=['count'])
            suspicion_matrix[self.required_params.provider_header] = suspicion_matrix.index
            suspicion_matrix.sort_values(['count', self.required_params.provider_header], axis=0, ascending=[False, True], inplace=True) # handle ties by ordering with provider ID
            self.pickle_data(suspicion_matrix, fname, True)

            return suspicion_matrix.index.tolist()

        provider_suspicions = {x: ranked_provider_info[x].suspicious_transactions_score for x in ranked_provider_info}
        matrix_name = f"suspicion_matrix_{rp.code_of_interest}_supp_{rp.min_support}"
        susp = save_ranked_results(provider_suspicions, matrix_name)
        surgeon_suspicions = {k: v.suspicious_transactions_score for k, v in ranked_provider_info.items() if v.provider_label == "Surgeon"}
        matrix_name = f"surgeon_matrix_{rp.code_of_interest}_supp_{rp.min_support}"
        save_ranked_results(surgeon_suspicions, matrix_name)

        self.log("Saving provider results")
        glob_filename = self.logger.get_file_path(f"{rp.code_of_interest}_suspicious_providers.xlsx")
        with xlsxwriter.Workbook(glob_filename) as xl:
            skipped = 0
            suspicious_component_id = [0] * (len(labeller.components) + 1)
            for idx, s in enumerate(susp):
                provider_results = ranked_provider_info[s]
                if provider_results.provider_label is None:
                    skipped += 1
                    continue

                if rp.save_from == Save.SAVE_X_FROM_EACH:
                    if all(x >= rp.no_to_save for x in suspicious_component_id):
                        break

                    if suspicious_component_id[provider_results.closest_component] >= rp.no_to_save:
                        continue
                elif rp.save_from == Save.SAVE_X_FROM_COMPONENT_OF_INTEREST:
                    if provider_results.closest_component != component_of_interest:
                        skipped += 1
                        continue

                    if idx - skipped >= rp.no_to_save:
                        break
                else:
                    if idx - skipped > rp.no_to_save:
                        break

                suspicious_component_id[provider_results.closest_component] += 1
                provider_results.rank = idx - skipped

                self.log(f"Rank {provider_results.rank} {provider_results.provider_label} provider {s} has the following RSPs")
                rsps = data.loc[data[rp.provider_header] == s, hc.PR_SP].unique().tolist()
                for rsp in rsps:
                    self.log(self.code_converter.convert_rsp_num(rsp))

                new_edit_attrs = self.save_graphs_to_images(provider_results)
                self.write_suspicions_to_file(new_edit_attrs, xl, provider_results, component_item_occurences)

        self.log("Saving aggregate results")
        all_suspicion_scores = [x.suspicious_transactions_score for x in ranked_provider_info.values()]
        self.plots.create_boxplot(all_suspicion_scores, f"{rp.code_of_interest} suspicion scores", "sus_box")
        provider_scores = [[] for x in range(len(labeller.components) + 1)]
        for provider_result in ranked_provider_info.values():
            provider_scores[provider_result.closest_component].append(provider_result.suspicious_transactions_score)

        sus_component_labels = list(labeller.component_label_converter.values())
        sus_component_labels[-1] = "None"
        sus_component_labels, provider_scores = zip(*sorted(zip(sus_component_labels, provider_scores)))

        for i, component in enumerate(provider_scores):
            self.log(f"Component {i}: {sus_component_labels[i]}")
            self.log(pd.Series(component).describe())

        self.plots.create_boxplot_group(provider_scores,
                                        sus_component_labels,
                                        "Scores per graph component",
                                        "sus_box_per_component")
        all_components = pd.DataFrame([x.closest_component for x in ranked_provider_info.values()])
        self.log(all_components.value_counts())
