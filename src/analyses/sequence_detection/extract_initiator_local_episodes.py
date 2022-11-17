'''Template for data analyses'''
import multiprocessing as mp
from dataclasses import dataclass
from datetime import timedelta
from statistics import median
import numpy as np
import pandas as pd
from overrides import overrides
from tqdm import tqdm
from src.core.algorithms.sequence.merger import MergeParameters
from src.analyses.sequence_detection.shared.containers import LppPatient, PatientLocalPatterns
from src.analyses.sequence_detection.shared.provider_info import get_ontology_information
from src.analyses.sequence_detection.shared.patient_interaction import PatientConverter
from src.core.base.base_analysis import AnalysisBase
import src.core.io.config as hc

class Analysis(AnalysisBase):
    '''Data analysis base class'''
    @dataclass
    class RequiredParams:
        '''Parameters required for the analysis'''
        category: int = 3
        group: str = 'T2'
        subgroup: int = 5
        max_period: int = 31
        min_duration: int = 1
        max_spill: int = 3
        ontology_of_interest: str = '3_T2'
        drop_no_initiator: bool = True
        patient_lpp_location: str = None
        n_processes: int = 5

    def __init__(self, logger, details, year):
        super().__init__(logger, details, year)
        rp = self.required_params
        self.codes_of_interest = self.code_converter.get_mbs_items_in_subgroup(rp.category, rp.group, rp.subgroup)
        self.course_parameters = self.create_merge_parameters()

    def create_merge_parameters(self):
        rp = self.required_params
        course_merge_parameters = MergeParameters()
        course_merge_parameters.drop_no_initiator_courses = rp.drop_no_initiator
        course_merge_parameters.max_initiator_timedelta = rp.max_period
        course_merge_parameters.max_period = rp.max_period
        course_merge_parameters.max_spill = rp.max_spill
        course_merge_parameters.min_duration = rp.min_duration

        return course_merge_parameters

    def parallel_lpp(self, arg):
        patient_id, patient_data = arg
        patient_lpp = PatientLocalPatterns(patient_id, patient_data, self.course_parameters)

        return patient_lpp

    def parallel_patients(self, patient_lpp):
        patient = LppPatient(patient_lpp, self.codes_of_interest)

        return patient

    @overrides
    def run_test(self) -> None:
        self.log("Running test")
        rp = self.required_params
        data = self.data

        lpp_filename = "patient_lpps.pkl"
        pool = mp.Pool(rp.n_processes)
        if rp.patient_lpp_location is None:
            self.log("Learning local periodic patterns")
            oncology = get_ontology_information(data, self.code_converter, rp.ontology_of_interest)
            oncology_providers = oncology[hc.PR_ID].unique().tolist()
            oncology_provider_data = data[data[hc.PR_ID].isin(oncology_providers)]
            patient_lpps = pool.map(self.parallel_lpp, oncology_provider_data.groupby(hc.PAT_ID)) # only care about claims from the oncologists
            self.pickle_data(patient_lpps, lpp_filename)
        else:
            file_location = f"{rp.patient_lpp_location}/{lpp_filename}"
            patient_lpps = self.unpickle_data(file_location, check_data_folder=False)

        self.log("Combining initiators")
        patients = pool.map(self.parallel_patients, patient_lpps)
        pool.close()
        pool.join()
        self.log("Saving data")
        patients = [x for x in patients if x.courses is not None]
        courses = [x for patient in patients for x in patient.courses]
        self.pickle_data(courses, "courses")
