'''run src'''
from operator import gt
from src.run_analysis import RunAnalysis
from src.core.base.base_analysis import AnalysisDetails

if __name__ == "__main__":
    analysis_runner = RunAnalysis("config.json")
    details = AnalysisDetails(
    notes="",
    params={},
    data_extract_specification = "sample_data",
    analysis_file_name='extract_initiator_local_episodes',
    # analysis_file_name='provider_pattern_comparison',
    # analysis_file_name='rule_combination',
    analysis_file_location="sequence_detection",
    years=["2014"]
    )

    analysis_runner.start(details)
