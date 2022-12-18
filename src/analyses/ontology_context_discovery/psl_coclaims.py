'''Template for data analyses'''
import random
from itertools import combinations
from dataclasses import dataclass
from math import exp
import numpy as np
import pandas as pd
from overrides import overrides
from scipy.stats import boxcox, percentileofscore
from tqdm import tqdm
from src.core.algorithms.stats import medcouple_1d
from src.core.base.base_analysis import AnalysisBase
import src.core.io.config as hc
from src.core.io.spark.spark_wrapper import SparkWrapper

class Analysis(AnalysisBase):
    '''Data analysis base class'''
    @dataclass
    class RequiredParams:
        '''Parameters required for the analysis'''
        providers_of_interest: str = ''
        dms_check: str = ''
        all_dms_providers: str = None
        start_date: str = "20194"
        end_date: str = "20204"

    @overrides
    def load_data(self, data_file, in_data_folder=True):
        data = super().load_data(data_file, in_data_folder)
        self.processed_data = data
        self.test_data = data

    def get_raw_counts(self, item_1, item_2, provider_counts, all_provider_counts):
        oc_val = []
        for l in all_provider_counts.values():
            try:
                oc_val.append(l[item_1][item_2])
            except KeyError:
                oc_val.append(0)

        s = pd.Series(oc_val)
        try:
            val = provider_counts[item_1][item_2]
        except KeyError:
            val = 0

        p = percentileofscore(s, val, kind='weak')
        non_zeros = s[s > 0]
        n_claiming = len(non_zeros)

        return (val, p, n_claiming), s

    def get_percentiles(self, s):
        q0 = s.min()
        q10 = s.quantile(0.1)
        q25 = s.quantile(0.25)
        q50 = s.quantile(0.50)
        q75 = s.quantile(0.75)
        q90 = s.quantile(0.90)
        q95 = s.quantile(0.95)
        q96 = s.quantile(0.96)
        q97 = s.quantile(0.97)
        q98 = s.quantile(0.98)
        q99 = s.quantile(0.99)
        q100 = s.max()

        return (q0, q10, q25, q50, q75, q90, q95, q96, q97, q98, q99, q100)

    def is_skewed_positive_outlier(self, s, n):
        non_zeros = s[s > 0]
        if len(non_zeros) <=10:
            return None

        mc = medcouple_1d(non_zeros)
        if mc == np.inf:
            return np.inf

        non_zero_q25 = non_zeros.quantile(0.25)
        non_zero_q75 = non_zeros.quantile(0.75)
        outlier_cutoff = non_zero_q75 + (1.5 * (exp(3 * mc)) * (non_zero_q75 - non_zero_q25))

        return n > outlier_cutoff

    def is_boxcox_outlier(self, s, percentile):
        non_zeros = s[s > 0]
        if len(non_zeros) <= 10 or len(non_zeros.unique()) == 1:
            return None

        trans, lam = boxcox(non_zeros)
        trans = pd.Series(trans)
        non_zero_q25 = trans.quantile(0.25)
        non_zero_q75 = trans.quantile(0.75)
        outlier_cutoff = non_zero_q75 + (3 * (non_zero_q75 - non_zero_q25))
        n = trans.quantile(percentile / 100)

        return n > outlier_cutoff

    def write_to_file(self, path, items, provider_results, provider_counts):
        header = ['Item','Provider claims','Provider percentile', 'Total providers with claim', "", "Min", "Q10", "Q25", "Median", "Q75", "Q90", "Q95", "Q96", "Q97", "Q98", "Q99", "Max", "", "Anomalous", "Log anomalous"]
        header = ','.join(header) + '\n'
        with open(path, 'w+') as f:
            f.write(header)
            for item in items:
                main_vals, s = self.get_raw_counts(item, item, provider_results, provider_counts)
                quantiles = self.get_percentiles(s)
                anomalous = self.is_skewed_positive_outlier(s, main_vals[0])
                anom2 = self.is_boxcox_outlier(s, main_vals[1])
                row = ','.join([item] + [str(x) for x in main_vals] + [""] + [str(x) for x in quantiles] + ["", str(anomalous), str(anom2)])
                f.write(row + '\n')

            for a, b in combinations(items, 2):
                main_vals, s = self.get_raw_counts(a, b, provider_results, provider_counts)
                quantiles = self.get_percentiles(s)
                if main_vals[0] == 0:
                    continue # don't record combinations which aren't claimed

                anomalous = self.is_skewed_positive_outlier(s, main_vals[0])
                row = ','.join([f"{a} {b}"] + [str(x) for x in main_vals] + [""] + [str(x) for x in quantiles] + ["", str(anomalous)])
                f.write(row + '\n')

    @overrides
    def run_test(self) -> None:
        self.log("Running test")
        rp = self.required_params
        data = self.test_data
        spark = SparkWrapper()
        if rp.dms_check is None:
            if path.suffix == '.csv':
                providers_of_interest = pd.read_csv(path, dtype=str)['0'].values.tolist()
            elif path.suffix == '.pkl':
                providers_of_interest = self.unpickle_data(path)
            else:
                raise ValueError("Unexpected file type in providers of interest")

            dms_of_interest = {}
            self.log("Getting providers")
            for provider in tqdm(provider_of_interest):
                dms_data = spark.get_provider_dms(provider, rp.start_date, rp.end_date)
                dms_path = self.logger.get_file_path(f"provider_{provider}_DMS_data.csv")
                dms_data.to_csv(dms_path)
                dms_names = dms_data["MJR_SPCLTY_NM"].unique().tolist()
                self.log(f"Provider {provider} had the following DMSs: {dms_names}")
                if len(dms_names) > 1:
                    raise ValueError("Expected 1 DMS only - code redesign required if DMS changes over the time period")

                dms = dms_names[0]
                dms_providers = dms_of_interest.get(dms, [])
                dms_providers.append(provider)
                dms_of_interest[dms] = dms_providers

            self.pickle_data(dms_of_interest, "DMS_check")
        else:
            path = self.get_project_root() / f"Output/{rp.dms_check}"
            dms_of_interest = self.unpickle_data(path)

        if rp.all_dms_providers is None:
            all_dms = {}
            for key in dms_of_interest:
                all_dms_providers = spark.get_dms_providers(key, rp.start_date, rp.end_date)
                all_dms[key] = all_dms_providers

            self.pickle_data(all_dms, "all_dms_providers")
        else:
            path = self.get_project_root() / f"Output/{rp.all_dms_providers}"
            all_dms = self.unpickle_data(path)

        for dms, dms_providers in tqdm(dms_of_interest.items()):
            all_dms_providers = all_dms[dms]
            dms_data = data[data[hc.PR_ID].isin(all_dms_providers)]
            dms_items = dms_data[hc.ITEM].unique().tolist()
            dms_counts = {}
            dms_provider_groups = dms_data.groupby(hc.PR_ID)
            skipped_count = 0
            for provider in tqdm(all_dms_providers):
                try:
                    info = dms_provider_groups.get_group(provider)
                except KeyError:
                    skipped_count += 1
                    continue # provider is in the DMS but not this dataset
                days = info.groupby("EventID")
                all_prov_items = info[hc.ITEM].unique().tolist()
                prov_counts = {x: {} for x in all_prov_items}
                for _, day in days:
                    items = day[hc.ITEM].unique().tolist()
                    for item_1 in items:
                        for item_2 in items:
                            i_count = prov_counts[item_1].get(item_2, 0)
                            i_count += 1
                            prov_counts[item_1][item_2] = i_count

                dms_counts[provider] = prov_counts

            self.log(f"{skipped_count} providers in the {dms} DMS but not in the ortho data")
            items_of_interest = set()
            for provider in tqdm(dms_providers):
                info = dms_provider_groups.get_group(provider)
                all_prov_items = info[hc.ITEM].unique().tolist()
                items_of_interest.update(all_prov_items)
                provider_counts = dms_counts[provider]
                file_dms = dms.replace('-', '_').replace(' ', '_')
                provider_path = self.logger.get_file_path(f"{file_dms}_provider_{provider}_coclaims.csv")
                self.write_to_file(provider_path, all_prov_items, provider_counts, dms_counts)

            items_of_interest = tuple(items_of_interest)
            for i in range(3):
                item = random.choice(items_of_interest)
                counts = []
                for provider, items in dms_counts.items():
                    try:
                        count = items[item][item]
                        counts.append(count)
                    except KeyError:
                        counts.append(0)

                output = f"histo_{dms}_item_{item}"
                self.plots.basic_histogram(counts, output, n_bins=10, title=f"Item {item}")
