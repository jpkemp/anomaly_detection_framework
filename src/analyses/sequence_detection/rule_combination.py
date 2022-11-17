'''Template for data analyses'''
from collections import Counter
from dataclasses import dataclass
from itertools import combinations
from functools import partial
import pandas as pd
from overrides import overrides
from tqdm import tqdm
from src.analyses.sequence_detection.shared.containers import ExtendedCourse, SequenceGraph
from src.analyses.sequence_detection.shared.containers.course_writer import WriteProviderCourses
from src.analyses.sequence_detection.shared.patient_interaction import PatientConverter
from src.core.base.base_analysis import AnalysisBase
import src.core.io.config as hc

class Analysis(AnalysisBase):
    '''Data analysis base class'''
    @dataclass
    class RequiredParams:
        '''Parameters required for the analysis'''
        course_results: str = 'src.analyses.sequence_detection_extract_initiator_local_episodes_XXXX'
        rule_folder: str = 'src.analyses.sequence_detection_provider_pattern_comparison_XXXX'
        context_name: str = "15550_15562" # select which results to examine
        save_n_providers: int = 10
        items_rare_below: float = 0.1
        # mbs_items: bool = False
        mbs_items: bool = True

    def __init__(self, logger, details, year):
        super().__init__(logger, details, year)
        rp = self.required_params
        file_path = f"Output/{rp.rule_folder}/suspicious_rules_{rp.context_name}.pkl"
        file_path = self.get_project_root() / file_path
        all_suspicious_rules = self.unpickle_data(file_path)

        file_path = f"Output/{rp.rule_folder}/rules_frequencies_{rp.context_name}.pkl"
        file_path = self.get_project_root() / file_path
        self.rule_quantiles = self.unpickle_data(file_path)
        file_path = f"Output/{rp.rule_folder}/provider_rules_{rp.context_name}.pkl"
        file_path = self.get_project_root() / file_path
        self.provider_rules = self.unpickle_data(file_path)

        file_path = f"Output/{rp.course_results}"
        file_path = self.get_project_root() / file_path / "courses.pkl"
        self.patients = self.unpickle_data(file_path)
        context_courses = PatientConverter.get_courses_by_context(self.patients)[rp.context_name]
        total_courses = len(context_courses)
        total_item_counts = {}
        for course in tqdm(context_courses):
            items = set(item for day in course.item_sequence.sequence for item in day.split(' '))
            for item in items:
                count = total_item_counts.get(item, 0)
                count += 1
                if rp.mbs_items:
                    total_item_counts[str(int(item))] = count
                else:
                    total_item_counts[item] = count

        filtered_rules = {}
        rare_items = set()
        rare_item_proportions = dict()
        for rule_name, rule in tqdm(all_suspicious_rules.items()):
            itemset = rule_name.split(' ')
            any_rare = False
            for items in itemset:
                for item in items.split('_'):
                    if rp.mbs_items:
                        proportion = total_item_counts[str(int(item))] / total_courses
                    else:
                        proportion = total_item_counts[item] / total_courses
                    is_rare = proportion < rp.items_rare_below
                    if is_rare:
                        any_rare = True
                        rare_items.add(item)
                        rare_item_proportions[item] = proportion

            if not any_rare:
                filtered_rules[rule_name] = rule

        self.filtered_rules = filtered_rules
        self.rare_items = rare_items
        self.rare_item_proportions = rare_item_proportions

    def convert_rule_name_to_ontology_location(self, rule_name):
        ont_location = []
        if self.required_params.mbs_items:
            ont_loc = self.code_converter.convert_mbs_code_to_ontology_label
        else:
            ont_loc = partial(self.code_converter.convert_pbs_code_to_atc_label, 5)

        for day in rule_name.split('_'):
            ont_day = []
            for item in day.split(' '):
                ont = (item)
                ont_day.append(ont)

            ont_location.append(' '.join(ont_day))

        return '_'.join(ont_location)

    @overrides
    def run_test(self) -> None:
        self.log("Running test")
        rp = self.required_params
        if rp.mbs_items:
            get_item_fee = self.code_converter.get_mbs_item_fee
        else:
            self.data["BNFT_AMT"] = self.data["BNFT_AMT"].astype(float)
            self.data['cost_per_unit'] = self.data["BNFT_AMT"] / self.data["PRSCRPTN_CNT"]
            cost_map = self.data.groupby(hc.ITEM).agg({'cost_per_unit': 'mean'}).to_dict()["cost_per_unit"]
            get_item_fee = lambda x: (cost_map[x], None)

        sequence_graphs = {}
        rule_names_by_length = {}
        rule_ontologies = {}
        rare_item_costs = {x: get_item_fee(x)[0] for x in self.rare_items}
        for rule_name in tqdm(self.rule_quantiles):
            graph = SequenceGraph.from_rule_name(rule_name, get_item_fee)
            sequence_graphs[rule_name] = graph
            current = rule_names_by_length.get(graph.total_items, [])
            current.append(rule_name)
            rule_names_by_length[graph.total_items] = current
            rule_ontologies[rule_name] = self.convert_rule_name_to_ontology_location(rule_name)

        labelled_courses_by_provider = {}
        provider_costs = {}
        updated_provider_rules = {}
        provider_cost_breakdowns = {}
        for provider_course_rules in tqdm(self.provider_rules):
            provider = provider_course_rules.id
            provider_cost = 0
            labelled_courses_by_provider[provider] = []
            replaced_rules = {}
            provider_graphs = []
            for rule_name in provider_course_rules.rules:
                if rule_name in self.filtered_rules \
                            and provider in self.filtered_rules[rule_name].provider_order:
                    rule = self.filtered_rules[rule_name]
                    idx = rule.provider_order.index(provider_course_rules.id)
                    prov_rate = rule.rates[idx]
                    graph = sequence_graphs[rule_name]
                    replaced_rules[rule_name] = graph.find_overclaimed_item_for_provider(
                        provider,
                        prov_rate,
                        rule_names_by_length,
                        sequence_graphs,
                        self.rule_quantiles,
                        rule_ontologies
                    )[0]
                    provider_graphs.append(graph)

            provider_cost_breakdown = Counter()
            for i, course in enumerate(provider_course_rules.courses):
                extended_course = ExtendedCourse(course)
                extended_course.label_rare_items(self.rare_items, rare_item_costs)
                for graph in provider_graphs:
                    if str(i) in provider_course_rules.rule_to_course[graph.name]:
                        extended_course.process_sequence_graph(provider,
                                                                graph)

                labelled_courses_by_provider[provider].append(extended_course)
                unusual_course_cost = extended_course.get_unusual_course_costs()
                provider_cost += unusual_course_cost
                provider_cost_breakdown.update(extended_course.item_costs)

            provider_course_rules.replaced_rules = replaced_rules
            updated_provider_rules[provider] = provider_course_rules
            provider_costs[provider] = provider_cost
            provider_cost_breakdowns[provider] = provider_cost_breakdown

        final_costs = pd.DataFrame.from_dict(provider_costs, orient='index', columns=['Costs'])
        self.pickle_data(final_costs, "final_costs")
        self.plots.create_boxplot(final_costs['Costs'].values.tolist(), "Cost distribution", "costs", axis_labels=["Providers", "Potentially recoverable costs ($)"], ext="svg")
        top_providers = final_costs.nlargest(rp.save_n_providers, 'Costs').to_records()
        for i, (provider, cost) in enumerate(top_providers):
            courses = labelled_courses_by_provider[provider]
            filename = self.logger.get_file_path(f"Rank {i} provider {provider} with cost {cost:.2f}.xlsx")
            WriteProviderCourses(filename,
                                 updated_provider_rules[provider],
                                 cost,
                                 i,
                                 courses,
                                 self.filtered_rules,
                                 self.rare_item_proportions,
                                 provider_cost_breakdowns[provider])

        all_providers = final_costs.sort_values("Costs", ascending=False)
        output = self.logger.get_file_path("Final rank.csv")
        all_providers.to_csv(output)
