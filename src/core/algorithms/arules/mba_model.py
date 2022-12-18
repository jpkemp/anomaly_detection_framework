'''MBA functions'''
import operator
import pickle
from tqdm import tqdm
from src.core.algorithms.arules.mba_comparisons import MbaComparisons
from src.core.algorithms.arules.pairwise_mba import PairwiseMba
from src.core.mbs_info.mbs_labeller import ComponentLabeller
from src.core.algorithms.graphs.mbs_graphs import MbsGraphColouring
from src.core.io.file_utils import FileUtils
from src.core.io import config as hc


class MbaModel():
    '''Class for holding data for MBA processed from MBS/PBS datasets'''
    def __init__(self,
                 logger,
                 code_converter,
                 filters):
        self.code_converter = code_converter
        self.graphs = MbsGraphColouring(logger, code_converter)
        self.logger = logger
        self.log = logger.log
        self.comparisons = MbaComparisons(code_converter, self.graphs)
        self.pairwise = PairwiseMba(filters)
        self.log("Initialising basic MBA groups")

    def create_model(self, items, documents, min_support, min_support_count=3):
        '''Create an MBA model'''
        d = self.pairwise.pairwise_market_basket(items,
                                                 documents,
                                                 min_support=min_support,
                                                 absolute_min_support_count=min_support_count,
                                                 max_p_value=1)

        return d

    def create_graph(self, d, name, title, attrs=None, graph_style='fdp', file_extension='png'):
        '''Create a visual graph from a graph dictionary'''
        filename = self.logger.output_path / f"{name}.{file_extension}"
        filters = self.pairwise.filters
        if filters['conviction']['value'] == 0 \
           and filters['confidence']['value'] == 0 \
           and (filters['certainty_factor']['value'] == 0 \
           and filters['certainty_factor']['operator'] == operator.ge):
            directed = False
        else:
            directed = True

        self.log(f"Graphing {title}")
        # self.graphs.visual_graph(d, filename, title=title, directed=directed, node_attrs=attrs, graph_style=graph_style)
        self.graphs.create_visnetwork(d, filename, title, attrs)

    def create_reference_model(self, min_support, name, documents, all_unique_items, node_labels, colour=True, graph_type=True, header=hc.ITEM):
        '''Commands related to creation, graphing and saving of the state models'''
        self.log(f"{len(documents)} transactions in {name}")
        self.log("Creating model")
        d = self.create_model(all_unique_items, documents, min_support)
        # remove no other item:
        if "No other items" in d:
            for k in d["No other items"]:
                if k not in d:
                    d[k] = {}

            d.pop("No other items")

        for k in d:
            d[k].pop("No other items", None)

        labeller = ComponentLabeller(d, node_labels, "Other")
        for i, g in enumerate(labeller.components):
            model_dict_csv = self.logger.get_file_path(f"{name}_model_component_{i}.csv")
            if graph_type:
                FileUtils.write_model_to_file(self.code_converter, g, model_dict_csv)

        title = f'Connections between items in {name}'

        if colour:
            formatted_d, attrs, legend = self.graphs.colour_mbs_codes(d)
        else:
            formatted_d, attrs, legend = self.graphs.convert_graph_and_attrs(d, header)

        model_name = self.logger.get_file_path(f"model_{name}.pkl")
        with open(model_name, "wb") as f:
            pickle.dump(formatted_d, f)

        attrs_name = self.logger.get_file_path(f"attrs_{name}.pkl")
        with open(attrs_name, "wb") as f:
            pickle.dump(attrs, f)

        legend_file = self.logger.get_file_path(f"Legend_{name}.png")
        if legend is not None:
            # self.graphs.graph_legend(legend, legend_file, "Legend")
            pass

        # self.graphs.create_visnetwork(formatted_d, name, title, attrs)
        self.create_graph(formatted_d, f"{name}.svg", title, attrs=attrs, file_extension="svg")

        return d, labeller

    def get_suspicious_ged(self, model, data, min_support, basket_header, attrs=None):
        '''Find suspicious graph variants from data'''
        def reset():
            c = ""
            u = set()
            d = []

            return c, u, d

        current_name, unique_items, documents = reset()

        all_graphs = {}
        suspicious_transactions = {}
        edit_graphs = {}
        edit_attrs = {}
        for name, group in tqdm(data):
            group_name, _ = name.split('__')
            if group_name != current_name:
                if current_name != '':
                    d = self.create_model(list(unique_items), documents, min_support)
                    all_graphs[int(current_name)] = d
                    ged, edit_d, edit_attr = self.graphs.graph_edit_distance(model, d, attrs)
                    edit_graphs[int(current_name)] = edit_d
                    edit_attrs[int(current_name)] = edit_attr
                    suspicious_transactions[int(current_name)] = ged

                current_name, unique_items, documents = reset()
                current_name = group_name

            documents.append(group[basket_header].unique().tolist())
            unique_items.update(group[basket_header])

        return suspicious_transactions, all_graphs, edit_graphs, edit_attrs

    def get_suspicious_transaction_score(self, d, data, basket_header, method='max', attrs=None, min_support=0.005):
        '''Create and score models from data'''
        if method == 'ged':
            suspicious_transactions, all_graphs, edit_graphs, edit_attrs = self.get_suspicious_ged(d,
                                                                                                   data,
                                                                                                   min_support,
                                                                                                   basket_header,
                                                                                                   attrs)

            return suspicious_transactions, all_graphs, edit_graphs, edit_attrs

        suspicious_transactions = {}
        for name, group in tqdm(data):
            # basket = [str(x) for x in group[self.basket_header].unique()]
            # missing = self.model.mba.check_basket_for_absences(basket, d)
            basket = [str(x) for x in group[basket_header]]
            if method == 'avg_thrsh' or method == 'imp_avg_thrsh' or method == 'max_prop':
                threshold = 10
            else:
                threshold = 0

            improper, proper = self.comparisons.check_basket_for_presences(basket, d, threshold=threshold)
            improper_len = len(improper)
            total_len = len(improper) + len(proper)
            if improper_len == 0:
                t = 0
            elif method == 'avg' or method == 'avg_thrsh':
                t = sum(list(improper.values())) / total_len
            elif method == 'imp_avg' or method == 'imp_avg_thrsh':
                t = sum(list(improper.values())) / improper_len
            elif method == 'max':
                t = max(list(improper.values()))
            elif method == 'max_prop':
                t = max(list(improper.values())) / total_len
            else:
                raise KeyError(f"{method} is not a scoring method")

            if t == 0:
                continue

            suspicious_transactions[name] = suspicious_transactions.get(name, 0) + t

        return suspicious_transactions
