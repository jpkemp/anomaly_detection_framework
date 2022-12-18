'''Tools to label providers and episodes'''
import pandas as pd
from src.core.algorithms.graphs.graph_utils import GraphUtils
from src.core.mbs_info.code_converter import CodeConverter

class EpisodeLabeller:
    def __init__(self, year):
        self.cdv = CodeConverter(year)
        self.surgeon_items = self.cdv.get_mbs_items_in_subgroup("3", "T8", "15")
        self.anaesthetist_items = self.cdv.get_mbs_items_in_group("3", "T10")

    def label_episode(self, episode):
        '''Label a list of items'''
        if any(x in self.surgeon_items for x in episode):
            return "Surgeon"
        elif any(x in self.anaesthetist_items for x in episode):
            return "Anaesthetist"
        elif "51300" in episode or "51303" in episode:
            return "Assistant"
        elif "105" in episode:
            return "Consultant"
        else:
            return "Other"

    def label_episode_by_max_fee(self, episode, level=2):
        fees = [self.cdv.get_mbs_item_fee(x)[0] for x in episode]
        df = pd.DataFrame([episode, fees], index=["Episode", "Fees"]).transpose()
        df = df.sort_values("Fees")
        max_item = df.iloc[0]
        ont = tuple(self.cdv.convert_mbs_code_to_group_labels(max_item["Episode"]))

        return ont[:level]

class ComponentLabeller:
    '''Used to label providers according to matching graph components'''
    def __init__(self, typical_model, specified_labels, other, error_on_multi=True):
        components = GraphUtils.graph_component_finder(typical_model)
        component_label_converter = {}
        for idx, component in enumerate(components):
            labelled = False
            for node, label in specified_labels:
                if node in component:
                    if labelled and label != component_label_converter[idx]:
                        if error_on_multi:
                            raise RuntimeWarning(f"Component {component} has labels {label} and comp")
                        else:
                            continue

                    component_label_converter[idx] = label
                    labelled = True

                if not labelled:
                    component_label_converter[idx] = other

        component_label_converter[len(component_label_converter)] = None
        self.component_label_converter = component_label_converter
        self.components = components

    def label_provider(self, provider_info):
        '''assign a rough label to providers based on items they claim'''
        closest_component = GraphUtils.identify_closest_component(self.components, provider_info.model_graph)
        provider_info.closest_component = closest_component
        provider_info.provider_label = self.component_label_converter[closest_component]
