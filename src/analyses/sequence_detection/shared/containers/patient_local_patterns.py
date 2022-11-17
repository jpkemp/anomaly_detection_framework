'''classes for holding extracted patient and episode information'''
from pandas import DataFrame
from src.core.algorithms.sequence.date_map import DateMap
from src.core.algorithms.sequence.format import FormatSpmf
from src.core.algorithms.sequence.merger import Merger, MergeParameters
from src.core.algorithms.sequence.sequence import SequentialPatternDetection as SPD
import src.core.io.config as hc

class PatientLocalPatterns:
    def __init__(self, patient_id: str, patient_data: DataFrame, parameters: MergeParameters, find_lpps=True, find_combined_patterns=True):
        self.id = patient_id
        self.data = patient_data
        self.date_map = DateMap(patient_data[hc.DATE])
        self.seq = FormatSpmf.construct_sequence(patient_data, patient_id, date_map=self.date_map, item_id="Ontology_cat", uniques_only_in_itemset=True)
        self.parameters = parameters
        if find_lpps:
            self.find_lpps()
        else:
            self.all_patterns = None
            self.all_timestamps = None

        if find_combined_patterns:
            self.combine_patterns()
        else:
            self.final_patterns = None
            self.final_timestamps = None

    def find_lpps(self):
        s = self
        p = self.parameters
        all_patterns, all_timestamps = SPD.mine_local_periodic_patterns(s.seq.sequence, s.seq.timestamps, p.max_period, p.min_duration, p.max_spill)
        self.all_patterns = all_patterns
        self.all_timestamps = all_timestamps

    def combine_patterns(self):
        p = self.parameters
        patterns, timestamps = SPD.combine_overlapping_timestamped_patterns(self.all_patterns, self.all_timestamps, tolerance=p.max_period)
        self.final_patterns = patterns
        self.final_timestamps = timestamps
