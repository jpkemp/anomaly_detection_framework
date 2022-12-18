'''Class for association analysis functions'''
import operator
import pandas as pd
from numpy import nan
from scipy.stats import fisher_exact

class PairwiseMba:
    '''Class for pairwise association analysis'''
    filters: dict = {
        'confidence': {
            'operator': operator.ge,
            'value': 0
        },
        'conviction': {
            'operator': operator.ge,
            'value': 0
        },
        'lift': {
            'operator': operator.ge,
            'value': 0
        },
        'odds_ratio': {
            'operator': operator.ge,
            'value': 0
        },
        'certainty_factor': {
            'operator': operator.ge,
            'value': -1
        }
    }

    def __init__(self, filters=None):
        self.update_filters(filters)

    def exception_rules(self, antecedent, consequent, threshold, documents):
        '''Find exception rules for an item pair'''
        X_subset = []
        item_subset = {}
        exclusions = []
        for doc in documents:
            if antecedent in doc:
                X_subset.append(doc)
                for item in doc:
                    item_subset[item] = item_subset.get(item, 0) + 1

        support_Y = item_subset[consequent] / len(X_subset)
        for item in list(item_subset.keys()):
            if item == consequent:
                continue

            support_X = item_subset[item] / len(X_subset)
            support_XY = 0
            for doc in X_subset:
                if consequent in doc and item in doc:
                    support_XY += 1

            support_XY = support_XY / len(X_subset)
            confidence = support_XY / support_X
            num = (1 - support_Y)
            den = (1 - confidence)
            conviction = num / den if den != 0 else 2 * threshold
            if conviction < threshold:
                exclusions.append(item)

        return exclusions

    def get_model_exception_rules(self, model, threshold, documents, ignore_list):
        '''Write exception rules to log file'''
        ret = []
        for antecedent in list(model.keys()):
            if antecedent in ignore_list:
                continue

            for consequent in list(model[antecedent].keys()):
                if consequent in ignore_list:
                    continue

                rules = self.exception_rules(antecedent, consequent, threshold, documents)
                if rules:
                    for e in rules:
                        r = (f"{antecedent} -> {consequent} -| {e}")
                        ret.append(r)

        return ret

    def pairwise_market_basket(self,
                               items,
                               documents,
                               min_support=0.1,
                               max_p_value=1,
                               absolute_min_support_count=0,
                               weight_edge_with='confidence'):
        '''find association rules between item pairs'''
        group_len = len(documents)
        if min_support < 1:
            min_occurrence = min_support * group_len
        else:
            min_occurrence = min_support

        if min_occurrence < absolute_min_support_count:
            min_occurrence = absolute_min_support_count

        reduced_items = {"No other items": 0}
        for item in items:
            reduced_items[item] = 0
        for doc in documents:
            for item in doc:
                reduced_items[item] += 1

        keys = list(reduced_items.keys())
        for item in keys:
            if reduced_items[item] < min_occurrence:
                reduced_items.pop(item)

        reduced_item_list = reduced_items.keys()
        counts = pd.DataFrame(0, index=reduced_item_list, columns=reduced_item_list)
        for doc in documents:
            for item in doc:
                if item not in reduced_item_list:
                    continue

                for item_2 in doc:
                    if item_2 not in reduced_item_list:
                        continue

                    counts.at[item, item_2] += 1

        # row_list = []
        d = {}
        for a in reduced_item_list:
            for b in reduced_item_list:
                if a == b:
                    continue

                count = counts.at[a, b]
                if  count >= min_occurrence:
                    f11 = count
                    f10 = reduced_items[a] - f11
                    f01 = reduced_items[b] - f11
                    f00 = group_len - (f10 + f01 + count)
                    odds_ratio, p_value = fisher_exact([[f11, f10], [f01, f00]], alternative='greater')
                    if odds_ratio is nan:
                        odds_ratio = 9999

                    if p_value > max_p_value:
                        continue

                    support = count / group_len
                    support_a = reduced_items[a] / group_len
                    support_b = reduced_items[b] / group_len

                    lift = support / (support_a * support_b)
                    confidence = support / support_a

                    conviction = (1 - support_b) / (1 - confidence) if confidence != 1 else 9999
                    if confidence > support_b:
                        certainty_factor = (confidence - support_b) / (1 - support_b) if support_b != 1 else 9999
                    elif confidence < support_b:
                        certainty_factor = (confidence - support_b) / support_b if support_b != 0 else 9999
                    else:
                        certainty_factor = 0

                    def get_interest_measure(k):
                        if k == 'lift':
                            fil = lift
                        elif k == 'confidence':
                            fil = confidence
                        elif k == 'conviction':
                            fil = conviction
                        elif k == 'odds_ratio':
                            fil = odds_ratio
                        elif k == 'certainty_factor':
                            fil = certainty_factor
                        else:
                            raise KeyError(f"No matching association rule {k}")

                        return fil

                    for k, v in self.filters.items():
                        comp = v['operator']
                        val = v['value']
                        fil = get_interest_measure(k)
                        if not comp(fil, val):
                            break
                    else:
                        if a not in d:
                            d[a] = {}

                        if weight_edge_with is None:
                            d[a][b] = {}
                        else:
                            d[a][b] = {"weight": get_interest_measure(weight_edge_with)}

        return d

    def update_filters(self, filters):
        '''Updates thresholds for interest measures'''
        if filters is None:
            raise RuntimeWarning("Please provide filters. To use default filters provide an empty dictionary")

        for k, v in filters.items():
            if k not in self.filters:
                raise KeyError(f"Invalid filter {k}")
            for key, val in v.items():
                if key not in self.filters[k]:
                    raise KeyError(f"Invalid {k} filter option {key}")
                self.filters[k][key] = val
