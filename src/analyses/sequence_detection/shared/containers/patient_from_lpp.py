'''classes for holding extracted patient and episode information'''
from dataclasses import dataclass
from src.core.algorithms.sequence.merger import Merger, MergeParameters
from src.analyses.sequence_detection.shared.containers.course_of_treatment import CourseOfTreatment
from src.analyses.sequence_detection.shared.containers.patient_local_patterns import PatientLocalPatterns
import src.core.io.config as hc

@dataclass
class LppPatient:
    '''container for extracted patient data'''
    def __init__(self, patient_local_patterns: PatientLocalPatterns, codes_of_interest):
        plp = patient_local_patterns
        self.id = plp.id
        if not plp.final_patterns:
            self.courses = None
            # assume initiator is at end of year - too close to have follow-up

            return

        self.date_map = plp.date_map
        max_timedelta = plp.parameters.max_initiator_timedelta
        drop_no_initiator = plp.parameters.drop_no_initiator_courses

        self.timestamps = self.process_initators(plp.data, plp.final_timestamps, plp.date_map, codes_of_interest, max_timedelta, drop_no_initiator)
        self.courses = self.extract_sub_episodes(plp.data, self.timestamps, plp.date_map, set(codes_of_interest), self.id)

    @classmethod
    def process_initators(cls, data, timestamps, date_map, codes_of_interest, max_interval, drop_no_initiator):
        initiator_rows = data[data[hc.ITEM].isin(codes_of_interest)]
        initiator_dates = initiator_rows[hc.DATE].apply(lambda x: date_map.get_timestamp_from_date(x)).values.tolist()
        new_timestamps = Merger.merge_initiator(initiator_dates, timestamps, max_interval, drop_no_initiator=drop_no_initiator)

        return new_timestamps

    @classmethod
    def extract_sub_episodes(cls, patient_data, timestamps, date_map, initiator_codes: set, patient_id):
        courses = []
        for timestamp in timestamps:
            start = date_map.get_date_from_timestamp(timestamp[0])
            end = date_map.get_date_from_timestamp(timestamp[1])
            mask = (patient_data[hc.DATE] >= start) & (patient_data[hc.DATE] <= end)
            sub = patient_data[mask].sort_values(hc.DATE)
            providers = sub[hc.PR_ID].unique().tolist()
            items = set(sub[hc.ITEM].unique().tolist())
            initiator_items = initiator_codes.intersection(items)
            initiator = '_'.join(sorted(list(initiator_items)))
            course = CourseOfTreatment(start, end, sub, f"{start}_{end}", providers, initiator, patient_id)
            courses.append(course)

        return courses


