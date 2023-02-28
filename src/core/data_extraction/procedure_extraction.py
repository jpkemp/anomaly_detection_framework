'''Tools for extracting procedures'''
import numpy as np
import pandas as pd
from tqdm import tqdm
from src.core.io import config as hc

class ProcedureExtractor():
    '''Data extraction functions'''
    def __init__(self, logger, code_converter):
        self.logger = logger
        self.log = logger.log
        self.code_converter = code_converter

    def exclude_multiple_states(self, data):
        '''Removes episodes with multiple states'''
        self.log("Removing episodes with multiple patient states")
        drop_index = False
        if "index" not in data.columns:
            data["index"] = data.index.values
            drop_index = True

        excluded = 0
        exclusions = []
        pats = data.groupby(hc.PAT_ID)
        for pat, info in tqdm(pats):
            episodes = info.groupby(hc.DATE)
            for episode, episode_info in episodes:
                n_states = len(episode_info[hc.GL].unique())
                if n_states > 1:
                    excluded += 1
                    self.log(f"Patient {pat} episode {episode} excluded for multiple states")
                    exclusions = exclusions + episode_info["index"].tolist()
                elif n_states == 0:
                    raise RuntimeError("This should never happen")

        valid_data = data.drop(exclusions)
        if drop_index:
            valid_data.drop("index", axis=1, inplace=True)

        self.log(f"{excluded} total patients excluded for multiple states")

        return valid_data

    def check_claim_validity(self, data):
        '''confirm claims have not been reversed'''
        self.log("Checking patient claim validity")
        data["index"] = data.index
        patients_to_check = data.loc[data[hc.VALID] != 1, hc.PAT_ID].unique().tolist()
        patient_groups = data.groupby(hc.PAT_ID)
        items_to_remove = []
        for patient_id in tqdm(patients_to_check):
            patient = patient_groups.get_group(patient_id)
            items_to_check = patient.loc[data[hc.VALID] != 1, hc.ITEM].unique(
            ).tolist()
            item_groups = patient[patient[hc.ITEM].isin(
                items_to_check)].groupby(hc.ITEM)
            for _, item_group in item_groups:
                dos_groups = item_group.groupby(hc.DATE)
                zero_date_indices = item_group.loc[item_group[hc.VALID] == 0, "index"].unique(
                ).tolist()
                items_to_remove.extend(zero_date_indices)

                neg_date = item_group.loc[item_group[hc.VALID]
                                          == -1, hc.DATE].unique().tolist()
                for date in neg_date:
                    date_claims = dos_groups.get_group(date)
                    date_total = date_claims[hc.VALID].sum()
                    indices = date_claims["index"].tolist()
                    if date_total == 0:
                        items_to_remove.extend(indices)
                    elif date_total < 0:
                        raise ValueError(
                            f"Patient {patient_id} has unusual claim reversals")
                    else:
                        mdvs = date_claims.loc[date_claims[hc.VALID]
                                               == -1, "index"].tolist()
                        items_to_remove.extend(mdvs)

        return data[~data["index"].isin(items_to_remove)].drop("index", axis=1)

    @classmethod
    def get_patient_of_interest_data(cls, codes_of_interest: list, data: pd.DataFrame):
        '''get data for patients who receive particular items'''
        idx = data[data[hc.ITEM].isin(codes_of_interest)].index
        patients_of_interest = data.loc[idx, hc.PAT_ID].unique().tolist()
        patient_data = data[data[hc.PAT_ID].isin(patients_of_interest)]
        patient_data.reset_index(inplace=True, drop=True)

        return patient_data

    @classmethod
    def get_providers_of_interest_data(cls, codes_of_interest: list, data: pd.DataFrame, provider_header=hc.PR_ID):
        '''get data for providers who claim particular items'''
        idx = data[data[hc.ITEM].isin(codes_of_interest)].index
        providers_of_interest = data.loc[idx, provider_header].unique().tolist()
        provider_data = data[data[provider_header].isin(providers_of_interest)]
        provider_data.reset_index(inplace=True, drop=True)

        return provider_data

    def get_same_day_claims(self,
                            codes_of_interest: list,
                            data: pd.DataFrame,
                            item_providers_only: bool,
                            check_validity: bool=True):
        '''get valid claims from one day for a patient, relating to a procedure code'''
        def get_subset(df):
            if item_providers_only:
                sub = self.get_patient_of_interest_data(codes_of_interest, df)
                return self.get_providers_of_interest_data(codes_of_interest, sub)
            else:
                return self.get_patient_of_interest_data(codes_of_interest, df)

        data_subset = get_subset(data)
        if check_validity:
            data_subset = self.check_claim_validity(data_subset)
            assert all(x == 1 for x in data_subset[hc.VALID].tolist()) # probably should write a unit test

        data_subset = get_subset(data_subset)
        data_subset["index"] = data_subset.index
        groups = data_subset.groupby(hc.PAT_ID)
        cols = data_subset.columns.tolist() + ["EventID"]
        final_data = pd.DataFrame(columns=cols)
        splits = 0
        for patient, group in tqdm(groups):
            dos = group.loc[group[hc.ITEM].isin(codes_of_interest), hc.DATE].unique().tolist()
            for i, check_date in enumerate(dos):
                indices = group.loc[group[hc.DATE] == check_date, "index"].tolist()
                assert len(indices) >= 1

                temp_df = data_subset[data_subset["index"].isin(indices)]
                temp_df["EventID"] = temp_df[hc.PAT_ID].astype(str) + f"_{check_date}"
                final_data = final_data.append(temp_df, ignore_index=True)

            splits += len(dos) - 1

        self.log(f"{len(groups)} starting patients")
        self.log(f"{splits} patients split")
        assert len(final_data["EventID"].unique()) == len(data_subset[hc.PAT_ID].unique()) \
                                                  + splits

        if final_data.empty:
            return pd.DataFrame(columns=cols).drop([hc.VALID], axis=1)

        return final_data.drop(["index", hc.VALID], axis=1)

    @classmethod
    def get_decision_making_providers(cls, data):
        return data.apply(lambda x: x['SPR'] if np.isnan(x[hc.RPR_ID]) else x[hc.RPR_ID], axis=1)

    @classmethod
    def exclude_less_than_x_occurrences(cls, data, x, col=hc.PR_ID, subcol=None):
        '''e.g. remove low-claim providers, or low-patient providers with subcol=hc.PAT_ID'''
        drop_index = False
        if "index" not in data.columns:
            data["index"] = data.index
            drop_index = True

        group = data.groupby(col)
        exclusions = []
        for _, info in tqdm(group):
            if subcol is None:
                if len(info) < x:
                    exclusions = exclusions + info["index"].tolist()
            else:
                if len(info.groupby(subcol)) < x:
                    exclusions = exclusions + info["index"].tolist()

        valid_data = data.drop(exclusions)
        if drop_index:
            data.drop("index", axis=1, inplace=True)
            valid_data.drop("index", axis=1, inplace=True)

        return valid_data
