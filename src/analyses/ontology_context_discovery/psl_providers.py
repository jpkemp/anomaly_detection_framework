'''Template for data analyses'''
from dataclasses import dataclass
import pandas as pd
from overrides import overrides
from tqdm import tqdm
from src.core.base.base_analysis import AnalysisBase
import src.core.io.config as hc
from src.core.io.spark.spark_wrapper import SparkWrapper

class Analysis(AnalysisBase):
    '''Data analysis base class'''
    @dataclass
    class RequiredParams:
        '''Parameters required for the analysis'''
        providers_of_interest: str = ''
        dms_check: str = None
        start_date: str = "20194"
        end_date: str = "20204"

    @overrides
    def run_test(self) -> None:
        self.log("Running test")
        rp = self.required_params
        data = self.test_data
        spark = SparkWrapper()
        if rp.dms_check is None:
            path = self.get_project_root() / f"Output/{rp.providers_of_interest}"
            if path.suffix == '.csv':
                providers_of_interest = pd.read_csv(path, dtype=str)['0'].values.tolist()
            elif path.suffix == '.pkl':
                providers_of_interest = self.unpickle_data(path)
            else:
                raise ValueError("Unexpected file type in providers of interest")

            dms_of_interest = {}
            self.log("Getting providers")
            for provider in tqdm(providers_of_interest):
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

        for dms, dms_providers in tqdm(dms_of_interest.items()):
            all_dms_providers = spark.get_dms_providers(dms, rp.start_date, rp.end_date)
            dms_data = data[data[hc.PR_ID].isin(all_dms_providers)]
            dms_counts = dms_data.groupby(hc.PR_ID)[hc.ITEM].value_counts().unstack(fill_value=0).transpose()
            dms_percentiles = dms_counts.rank(pct=True)
            describe = dms_counts.transpose().describe().transpose()
            for provider in tqdm(dms_providers):
                provider_counts = dms_counts[provider]
                items_of_interest = pd.DataFrame(provider_counts[provider_counts > 0])
                items_of_interest.columns = ['Count']
                provider_percentiles = pd.DataFrame(dms_percentiles[provider])
                provider_percentiles.columns = ['Percentile']
                percentiles_of_interest = items_of_interest.join(provider_percentiles, how='left')
                sums = pd.DataFrame(dms_counts.sum(axis=1))
                sums.columns=['n']
                percentiles_of_interest = percentiles_of_interest.join(sums, how='left')
                percentiles_of_interest = percentiles_of_interest.join(describe, how='left')
                percentiles_of_interest.sort_values('Count', inplace=True, ascending=False)

                file_dms = dms.replace('-', '_').replace(' ', '_')
                provider_path = self.logger.get_file_path(f"{file_dms}_provider_{provider}_percentiles.csv")
                percentiles_of_interest.to_csv(provider_path)

