'''Association analysis functions'''
class MbaComparisons:
    '''Functions for comparing arule transactions to graphs'''
    def __init__(self, code_converter, graphs):
        self.code_converter = code_converter
        self.graphs = graphs

    def compare_transaction_to_model(self, items, model):
        '''compare the items in a single transaction to a graph dictionary model'''
        _items = {}
        for i in items:
            if i not in _items:
                _items[i] = {}

        diamonds = []
        for k in model.keys():
            if k in _items:
                for key in model[k].keys():
                    if key not in _items:
                        diamonds.append(key)
                        _items[k][key] = {'color': 'red'}
                    else:
                        _items[k][key] = None

        return _items, diamonds

    def find_repeated_abnormal_nodes(self, non_unique_basket, model, threshold=10):
        '''find nodes that occur repeatedly in the basket, but not in the model'''
        improper, _ = self.check_basket_for_presences(non_unique_basket, model)
        basket = list(set(non_unique_basket))
        diamonds = []
        for k in basket:
            if improper.get(k, -1) > threshold:
                diamonds.append(k)

        return diamonds

    def check_basket_for_absences(self, basket, model):
        '''find nodes in the model missing in the basket'''
        tally = 0
        for item in model.keys():
            if item in basket:
                for expected_item in model[item].keys():
                    if expected_item not in basket:
                        tally += 1
        return tally

    def check_basket_for_presences(self, basket, model, threshold=0):
        '''find nodes in the basket missing in the model'''
        # two problems - unique item differences, and repeated item differences
        tally = {i: 0 for i in set(basket)}
        nodes = self.graphs.flatten_graph_dict(model)
        for item in basket:
            if item in nodes:
                tally[item] -= 1
            else:
                tally[item] += 1

        proper = {}
        improper = {}
        for k, v in tally.items():
            x = proper if v < threshold + 1 else improper
            x[k] = abs(v)

        return improper, proper
