'''similarity calculations'''
from typing import List
from math import log
import pandas as pd
from numpy import NaN
from rpy2.robjects import pandas2ri
from rpy2.robjects.packages import importr


def average_overlap(s: list, t: list):
    '''returns the average overlap of two equal-length lists of rankings'''
    if len(s) != len(t):
        raise NotImplementedError("AO not implemented for lists of different lengths")

    summation = 0
    k = len(s)
    for d in range(1, k+1):
        S = set(s[:d])
        T = set(t[:d])
        overlap = S.intersection(T)
        fraction = len(overlap) / d
        summation += fraction

    return summation / k

def rbo(s: list, t: list, p: float):
    '''returns the rank-biased overlap of two equal-length lists of rankings, weighted by p'''
    if len(s) != len(t):
        raise NotImplementedError("RBO not implemented for lists of different lengths")

    summation = 0
    k = len(s)
    for d in range(1, k+1):
        S = set(s[:d])
        T = set(t[:d])
        overlap = S.intersection(T)
        p_d = p ** (d - 1)
        fraction = p_d * len(overlap) / d
        summation += fraction

    return (1 -p) * summation

def rbo_with_ties(s: list, t: list, p: float):
    '''returns the rank-biased overlap of two equal-length lists of lists of rankings, weighted by p
       each list should be a list of lists, with ties placed inside the sublist
       empty sublists follow for the number of ties'''
    if len(s) != len(t):
        raise NotImplementedError("RBO not implemented for lists of different lengths")

    summation = 0
    k = len(s)
    for d in range(1, k+1):
        S = set([x for l in s[:d] for x in l])
        T = set([x for l in t[:d] for x in l])
        overlap = S.intersection(T)
        p_d = p ** (d - 1)
        fraction = p_d * 2 * len(overlap) / (len(S) + len(T))
        summation += fraction

    return (1 -p) * summation

def convert_series_to_tied_list(series: pd.Series) -> List[List]:
    '''Convert a pandas series to a tied list suitable for rbo_with_ties of the index values,
       using the series values to determine rank'''
    series = series.sort_values(ascending=False)
    ret = []
    current_score = series.max()
    current_idxs = []
    for (idx, val) in series.items():
        if val != current_score:
            ret.append(current_idxs)
            for _ in range(len(current_idxs) - 1):
                ret.append([])

            current_idxs = []
            current_score = val

        current_idxs.append(idx)

    ret.append(current_idxs)
    for _ in range(len(current_idxs) - 1):
        ret.append([])

    return ret

def rbo_weight_at_depth(p, depth):
    left_part = 1 - p**(depth - 1)
    mid_part = (1 - p) * depth / p
    right_part_left = log(1 / (1 - p))
    right_part_right = 0
    for i in range(1, depth):
        right_part_right += p**i / i

    return left_part + mid_part * (right_part_left - right_part_right)
def one_way_anova(df, output_path, index_name="index"):
    melt = pd.melt(df.reset_index(), id_vars=["index"], value_vars=df.columns)
    res = pg.rm_anova(dv="value", within="variable", subject="index", data=melt, detailed=True)
    path = output_path / 'pingouin_rm_anova.csv'
    res.to_csv(path)
