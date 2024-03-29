'''run src'''
from operator import gt
from src.run_analysis import RunAnalysis
from src.core.base.base_analysis import AnalysisDetails

if __name__ == "__main__":
    analysis_runner = RunAnalysis("config.json")
    details = AnalysisDetails(
    notes="",
    params={
        "filters": {
            'conviction': {
                'operator': gt,
                'value': 1
            }
        }
    },
    data_extract_specification = "sample_data",

    ##### GAA #####
    analysis_file_location="graphical_association_analysis",
    analysis_file_name='provider_ranking',

    ###### ontology context discovery ######
    # analysis_file_location="ontology_context_discovery",
    # analysis_file_name='role_costs',

    ###### sequential pattern mining ######
    # analysis_file_location="sequence_detection",
    # analysis_file_name='extract_initiator_local_episodes',
    # analysis_file_name='provider_pattern_comparison',
    # analysis_file_name='rule_combination',

    years=["2014"]
    )

    analysis_runner.start(details)
