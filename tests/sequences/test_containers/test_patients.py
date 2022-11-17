import unittest
from datetime import datetime as dt
import pandas as pd

from src.core.io.file_utils import FileUtils
FileUtils.update_config('./config.json')
import src.core.io.config as hc

from src.analyses.sequence_detection.shared.containers.patient_from_claims import ClaimsPatient
from src.analyses.sequence_detection.shared.containers.patient_from_lpp import LppPatient
from src.analyses.sequence_detection.shared.containers.patient_local_patterns import PatientLocalPatterns
from src.core.algorithms.sequence.date_map import DateMap
from src.core.algorithms.sequence.merger import MergeParameters
from src.core.mbs_info.code_converter import CodeConverter
from src.analyses.sequence_detection.shared.provider_info import get_ontology_information

cdv = CodeConverter(2014)
def format_data(data_dict):
        data = pd.DataFrame.from_dict(data_dict)
        data[hc.DATE] = pd.to_datetime(data[hc.DATE], format="%d-%b-%y")
        data[hc.ITEM] = data[hc.ITEM].astype(str)

        return data

class SequenceContainersTest(unittest.TestCase):
    def setUp(self):
        pat_1_items = [15524, 15506, 15700, 15242, 15242, 15242, 15242, 15242, 15242, 15242, 15242, 15242, 15242]
        pat_1_costs = [56115, 39555, 3910, 8300, 8300, 8300, 8300, 8300, 8300, 8300, 8300, 8300, 8300]
        pat_1_dates = ['21-Apr-14', '28-Apr-14', '29-Apr-14', '29-Apr-14', '30-Apr-14', '1-May-14', '2-May-14', '5-May-14', '6-May-14', '7-May-14', '8-May-14', '12-May-14', '13-May-14']
        mock_patient_1 = {
            hc.PAT_ID: ["test_1"] * len(pat_1_items),
            hc.PR_ID: ["prov_1"] * len(pat_1_items),
            hc.ITEM: pat_1_items,
            hc.COST: pat_1_costs,
            hc.DATE: pat_1_dates
        }
        self.mock_patient_1 = format_data(mock_patient_1)

        pat_2_items = [15230, 15260, 15230, 15230, 15524, 15230, 15506, 15230, 105, 15230, 104, 15700, 15230, 15230, 15230, 15230]
        pat_2_costs = [8300, 8300, 8300, 8300, 56115, 8300, 39555, 8300, 3655, 8300, 7275, 3910, 8300, 8300, 8300, 8300]
        pat_2_dates = ['16-Apr-14', '14-Apr-14', '22-Apr-14', '23-Apr-14', '28-Mar-14', '10-Apr-14', '28-Mar-14', '15-Apr-14', '27-Mar-14', '17-Apr-14', '5-Feb-14', '8-Apr-14', '9-Apr-14', '8-Apr-14', '18-Apr-14', "18-Jun-14"]
        n = len(pat_2_items)
        n_half = int(n / 2)
        mock_patient_2 = {
            hc.PAT_ID: ["test_2"] * n,
            hc.PR_ID: ["prov_2"] * n_half + ["prov_3"] * n_half,
            hc.ITEM: pat_2_items,
            hc.COST: pat_2_costs,
            hc.DATE: pat_2_dates
        }
        self.mock_patient_2 = format_data(mock_patient_2)


        pat_3_items = [105, 105, 872, 105, 872, 15562, 15230, 15260, 15230, 15230, 15524, 15230, 15506, 15230, 105, 15230, 104, 15700, 15230, 15230, 15230, 15230]
        pat_3_costs = [50, 50, 70, 50, 70, 3000, 8300, 8300, 8300, 8300, 56115, 8300, 39555, 8300, 3655, 8300, 7275, 3910, 8300, 8300, 8300, 8300]
        pat_3_dates = ['05-Apr-14', '05-Apr-14', '06-Apr-14', '07-Apr-14', '08-Apr-14', '15-Apr-14', '16-Apr-14', '14-Apr-14', '22-Apr-14', '23-Apr-14', '28-Mar-14', '10-Apr-14', '28-Mar-14', '15-Apr-14', '27-Mar-14', '17-Apr-14', '5-Feb-14', '8-Apr-14', '9-Apr-14', '8-Apr-14', '18-Apr-14', "18-Jun-14"]
        n = len(pat_3_items)
        n_half = int(n / 2)
        mock_patient_3 = {
            hc.PAT_ID: ["test_3"] * n,
            hc.PR_ID: ["prov_2"] * n_half + ["prov_3"] * n_half,
            hc.ITEM: pat_3_items,
            hc.COST: pat_3_costs,
            hc.DATE: pat_3_dates
        }
        self.mock_patient_3 = format_data(mock_patient_3)

    def test_patient_creation(self):
        test_parameters = MergeParameters()
        test_parameters.drop_no_initiator_courses = True
        test_parameters.max_initiator_timedelta = 7
        test_parameters.max_period = 2
        test_parameters.max_spill = 0
        test_parameters.min_duration = 1

        expected_timestamps_1 = [(9, 12), (15, 18), (22, 23)]
        final_timestamps_1 = [(8, 18)]
        final_sequence_1 = [['15506', '15242 15700', '15242', '15242', '15242', '15242', '15242', '15242', '15242']]
        expected_timestamps_2 = [(63, 65), (69, 73), (77, 78)]
        final_timestamps_2 = []
        final_sequence_2 = []
        expected_timestamps_3 = [(60, 65), (69, 73), (77, 78)] # note the first date is 05-Apr not 08-Apr because of the repetition of claims from the attendance section
        final_timestamps_3 = [(69, 78)]
        final_sequence_3 = [['15260', '15230 15562', '15230', '15230', '15230', '15230', '15230']]

        plps = []
        for pat, exp_time, final_time, final_seq in [(self.mock_patient_1, expected_timestamps_1, final_timestamps_1, final_sequence_1),
                         (self.mock_patient_2, expected_timestamps_2, final_timestamps_2, final_sequence_2),
                         (self.mock_patient_3, expected_timestamps_3, final_timestamps_3, final_sequence_3)]:
            date_map = DateMap(pat[hc.DATE])
            get_ontology_information(pat, cdv, "3_T2") # don't need the return value here because I don't need to extract the oncology providers
            # test PLP
            plp = PatientLocalPatterns("test_x", pat, test_parameters)
            plps.append(plp)
            self.assertEqual(len(plp.final_timestamps), len(exp_time))
            # self.assertEqual(len(plp.final_patterns), len(exp_pattern)) # patterns uses pandas categorical mapping
            for i, tup in enumerate(exp_time):
                test = plp.final_timestamps[i]
                self.assertEqual(test[0], tup[0])
                self.assertEqual(test[1], tup[1])

            # test patient and course
            pat_container = LppPatient(plp, ['15506', '15524', '15562'])
            self.assertEqual(len(pat_container.courses), len(final_seq))
            for i, course in enumerate(pat_container.courses):
                self.assertEqual(course.start, date_map.get_date_from_timestamp(final_time[i][0]))
                self.assertEqual(course.end, date_map.get_date_from_timestamp(final_time[i][1]))
                self.assertEqual(len(course.item_sequence.sequence), len(final_seq[i]))
                for j, val in enumerate(final_seq[i]):
                    self.assertEqual(val, course.item_sequence.sequence[j])

