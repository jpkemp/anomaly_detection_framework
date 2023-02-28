'''Template for data analyses'''
import multiprocessing as mp
from dataclasses import dataclass, field
from functools import partial
from typing import List
import pandas as pd
from overrides import overrides
from tqdm import tqdm
from src.core.base.base_analysis import AnalysisBase
from src.analyses.sequence_detection.shared.containers import ProviderCourseRules, UnusualSequenceRule
from src.analyses.sequence_detection.shared.patient_interaction import PatientConverter
import src.core.io.config as hc

class Analysis(AnalysisBase):
    '''Data analysis base class'''
    @dataclass
    class RequiredParams:
        '''Parameters required for the analysis'''
        course_results: str = 'src.analyses.sequence_detection_extract_initiator_local_episodes_XXXX'
        support: float = 0.03
        max_length: int = 3
        gap: int = 1
        skip_providers_with_less_than_x_courses: int = 20
        skip_groups_with_less_than_x_providers: int = 20
        ignore_rates_below_x: float = 0.05
        n_processes: int = 10
        mbs_items: bool = True
        plot_contexts_of_interest: list = field(default_factory=lambda: ['15565'])

    def __init__(self, logger, details, year):
        super().__init__(logger, details, year)
        rp = self.required_params
        self.args = [1, rp.max_length, "", rp.gap, True]

    @staticmethod
    def process_suspicious_rules(provider_course_rules: List[ProviderCourseRules], ignore_rates_below, ontology_converter, cost_converter):
        n_providers = len(provider_course_rules)
        rule_counts = {}
        rule_quantiles = {}
        suspicious_rules = {}
        provider_order = {}
        provider_courses = {}
        for provider in tqdm(provider_course_rules):
            provider_courses[provider.id] = provider.n_courses
            for rule in provider.rules:
                current_count = rule_counts.get(rule, [])
                current_count.append(provider.get_proportional_rule_occurrence(rule))
                rule_counts[rule] = current_count
                current_order = provider_order.get(rule, [])
                current_order.append(provider.id)
                provider_order[rule] = current_order

        for rule, counts in tqdm(rule_counts.items()):
            zero_providers = n_providers - len(counts)
            counts = counts
            quant_counts = pd.Series(counts + ([0] * zero_providers))
            q100 = quant_counts.quantile(1)
            q95 = quant_counts.quantile(0.95)
            q90 = quant_counts.quantile(0.9)
            q3 = quant_counts.quantile(0.75)
            q1 = quant_counts.quantile(0.25)
            med = quant_counts.quantile(0.5)
            iqr = q3 - q1
            outlier = q3 + 3 * iqr

            rule_quantiles[rule] = {"25": q1, "50": med, "75": q3, "90": q90, "95": q95, "100": q100}
            for i, value in enumerate(counts):
                if value < ignore_rates_below:
                    continue

                if value > outlier:
                    temp = suspicious_rules.get(rule, UnusualSequenceRule(rule, rule_quantiles[rule], ontology_converter, cost_converter))
                    provider = provider_order[rule][i]
                    temp.add_provider(provider, value, provider_courses[provider])
                    suspicious_rules[rule] = temp

        return suspicious_rules, rule_quantiles

    def process_context_courses(self, args):
        course_grouping, courses = args
        provider_courses = PatientConverter.get_provider_courses(courses)
        n_providers = len(provider_courses)
        skip = self.required_params.skip_providers_with_less_than_x_courses
        if n_providers < self.required_params.skip_groups_with_less_than_x_providers:
            self.log(f"Course group {course_grouping} only had {len(provider_courses)} providers and was skipped")
            return

        n_per_provider = [len(x) for x in provider_courses.values()]
        provider_results = []
        for provider, courses in tqdm(provider_courses.items()):
            n_courses = len(courses)
            if n_courses < skip:
                continue

            minsup = max(round(100 * 3 / n_courses, 1), round(100 * self.required_params.support, 1))
            params = [f"{minsup}%"] + self.args
            provider_result = ProviderCourseRules(provider, course_grouping, courses, params)
            provider_results.append(provider_result)

        valid_results = len(provider_results)
        total_results = len(provider_courses)
        dropped_providers = total_results - valid_results
        self.log(f"{dropped_providers} of {total_results} relevant providers had fewer than {skip} courses of treatment in the {course_grouping} group")

        suspicious_rules, rule_quantiles = self.process_suspicious_rules(provider_results, self.required_params.ignore_rates_below_x, self.get_ontology, self.get_item_fee)
        if suspicious_rules:
            output_file = self.logger.get_file_path(f"suspicious_rules_{course_grouping}")
            self.pickle_data(suspicious_rules, output_file)
            output_file = self.logger.get_file_path(f"rules_frequencies_{course_grouping}")
            self.pickle_data(rule_quantiles, output_file)
            provider_results_dict = {x.id: x for x in provider_results}
            self.pickle_data(provider_results, f"provider_rules_{course_grouping}")

        return (n_providers, n_per_provider)

    @overrides
    def run_test(self) -> None:
        self.log("Running test")
        rp = self.required_params
        if rp.mbs_items:
            self.get_item_fee = self.code_converter.get_mbs_item_fee
            self.get_ontology = self.code_converter.convert_mbs_code_to_ontology_label
        else:
            self.data["BNFT_AMT"] = self.data["BNFT_AMT"].astype(float)
            self.data['cost_per_unit'] = self.data["BNFT_AMT"] / self.data["PRSCRPTN_CNT"]
            cost_map = self.data.groupby(hc.ITEM).agg({'cost_per_unit': 'mean'}).to_dict()["cost_per_unit"]
            self.get_item_fee = lambda x: (cost_map[x], None)
            self.get_ontology = partial(self.code_converter.convert_pbs_code_to_atc_label, 5)

        data = self.data
        unique_items = data[hc.ITEM].unique().tolist()
        course_path = f"{self.get_project_root()}/Output/{rp.course_results}/courses.pkl"
        courses = self.unpickle_data(course_path, check_data_folder=False)
        course_groups = PatientConverter.get_courses_by_context(courses)
        course_groups = [(key, val) for key, val in course_groups.items()]
        self.log(f"{len(course_groups)} contexts identified")
        n_processes = min(rp.n_processes, len(course_groups))
        if n_processes:
            pool = mp.Pool(processes=n_processes)
            pooled_results = pool.map(self.process_context_courses, course_groups)
            pool.close()
            pool.join()
        else:
            pooled_results = []
            for args in course_groups:
                pooled_results.append(self.process_context_courses(args))

        context_labels = []
        courses_per_provider = []
        for i, n in enumerate(pooled_results):
            if n is None:
                continue

            context = course_groups[i][0]
            if rp.plot_contexts_of_interest is not None:
                if not any(x in context for x in rp.plot_contexts_of_interest):
                    continue

            label = f"{context.replace('_', '+')}, {n[0]} providers"
            context_labels.append(label)
            courses_per_provider.append(n[1])

        self.plots.create_boxplot_group(courses_per_provider, context_labels, "Courses per provider in each context", "per_provider_box")
        context_counts = [len(x[1]) for x in course_groups]
        self.log(f"{len(course_groups)} total contexts discovered")
        lots_of_courses = [x for x in context_counts if x > 500]
        self.log(f"{len(lots_of_courses)} contexts discovered")
        for x in lots_of_courses:
            self.log(x)
        self.plots.create_boxplot(context_counts, "Context counts", "per_context_box", axis_labels=["","Courses per context"], ext="svg")

