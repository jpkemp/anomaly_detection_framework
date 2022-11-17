from dataclasses import dataclass
from src.analyses.sequence_detection.shared.containers import CourseOfTreatment
from src.core.algorithms.sequence.format import FormatSpmf
import src.core.io.config as hc

@dataclass
class ClaimsPatient:
    def __init__(self, patient_id, patient_data, codes_of_interest):
        self.id = patient_id
        self.date_map = FormatSpmf.create_date_map(patient_data[hc.DATE])
        dates = [patient_data[hc.DATE].min(), patient_data[hc.DATE].max()]
        self.timestamps = [tuple([self.date_map.get_timestamp_from_date(x) for x in dates])]
        self.courses = self.extract_sub_episodes(patient_data, self.timestamps, self.date_map, self.id)

    @classmethod
    def extract_sub_episodes(cls, patient_data, timestamps, date_map,  patient_id):
        courses = []
        for timestamp in timestamps:
            start = date_map.get_date_from_timestamp(timestamp[0])
            end = date_map.get_date_from_timestamp(timestamp[1])
            mask = (patient_data[hc.DATE] >= start) & (patient_data[hc.DATE] <= end)
            sub = patient_data[mask].sort_values(hc.DATE)
            providers = sub[hc.PR_ID].unique().tolist()
            items = set(sub[hc.ITEM].unique().tolist())
            context = "claims"
            course = CourseOfTreatment(start, end, sub, f"{start}_{end}", providers, context, patient_id)
            courses.append(course)

        return courses



