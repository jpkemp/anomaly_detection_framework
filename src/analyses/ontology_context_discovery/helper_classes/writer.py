from itertools import combinations
import pandas as pd
from scipy.stats import percentileofscore
class Writer:
    @classmethod
    def get_item_occurrences(cls, co_occurrence: dict, provider_counts: dict, item_1: str, item_2: str):
        oc_val = []
        try:
            val = provider_counts[item_1][item_2]
        except KeyError:
            return None, None

        for providers in co_occurrence.values():
            try:
                oc_val.append(providers[item_1][item_2])
            except KeyError:
                oc_val.append(0)

        s = pd.Series(oc_val)
        p = percentileofscore(s, val, kind='weak')
        n_claiming = len(s[s > 0])

        return (val, p, n_claiming), s

    @classmethod
    def get_percentiles(cls, s):
        q10 = s.quantile(0.1)
        q25 = s.quantile(0.25)
        q50 = s.quantile(0.50)
        q75 = s.quantile(0.75)
        q90 = s.quantile(0.90)

        return (q10, q25, q50, q75, q90)

    @classmethod
    def write_to_file(cls, f, co_occurrence, provider_counts):
        items = list(provider_counts.keys())
        header = ','.join(['Item',
                           'Provider claims',
                           'Provider percentile',
                           'Total providers with claim',
                           "",
                           "Q10",
                           "Q25",
                           "Median",
                           "Q75",
                           "Q90"])
        f.write(header + '\n')
        for item in items:
            main_vals, s = cls.get_item_occurrences(co_occurrence, provider_counts, item, item)
            quantiles = cls.get_percentiles(s)
            row = ','.join([item] + [str(x) for x in main_vals] + [""] + [str(x) for x in quantiles])
            f.write(row + '\n')

        for a, b in combinations(items, 2):
            main_vals, s = cls.get_item_occurrences(co_occurrence, provider_counts, a, b)
            if main_vals is None:
                continue # don't record combinations which aren't claimed

            quantiles = cls.get_percentiles(s)
            row = ','.join([f"{a} {b}"] + [str(x) for x in main_vals] + [""] + [str(x) for x in quantiles])
            f.write(row + '\n')
