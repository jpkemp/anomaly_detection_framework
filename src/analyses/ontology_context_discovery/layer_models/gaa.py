from itertools import combinations
from overrides import overrides
from src.analyses.cost_prediction.shared.data_extraction import create_document_vectors
from src.core.algorithms.arules.mba_model import MbaModel
from src.core.data_extraction.data_grouper import DataGrouper
from src.subheading_role_costs.helper_classes.role import Role
from src.subheading_role_costs.layer_models.base import AbstractLayerModel, NoModelError

class GaaRoles(AbstractLayerModel):
    '''Data analysis base class'''
    @staticmethod
    @overrides
    def create_role_data(test_case, log, label, subheadings) -> None:
        s = subheadings
        mba = MbaModel(test_case.logger, test_case.code_converter, test_case.required_params.filters)
        s.model, _ = mba.create_reference_model(0.05, s.label, s.episodes, s.unique_onts, s.node_labels,
            colour=False,graph_type=False,header="EventID")
        if not s.model:
            raise NoModelError

        components = test_case.graphs.find_graph_components(s.model)
        sorted_components = sorted([sorted(x) for x in components])
        s.components = sorted_components
        log(s.components)
        s.role_data = {r: Role(r) for r in range(len(s.components) + 1)}
        for i, ep in enumerate(s.episodes):
            d = {x: {} for x in ep}
            role = test_case.graphs.identify_closest_component(s.components, d)
            s.roles.append(role)
            s.role_data[role].fees.append(s.fees[i])
