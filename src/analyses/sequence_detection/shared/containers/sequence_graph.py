from itertools import combinations
from typing import Callable

class SequenceGraph:
    def __init__(self, name:str, get_item_fee: Callable, *days: list):
        self.sequence = []
        self.name = name
        total_items = 0
        unique_items = set()
        for day in days:
            item_counts = {}
            for item in day:
                count = item_counts.get(item, 0)
                count += 1
                item_counts[item] = count
                unique_items.add(item)
                total_items += 1

            self.sequence.append(item_counts)

        self.n_days = len(self.sequence)
        self.total_items = total_items
        self.replacement_rule = {}
        self.unusual_positions = None
        self.get_item_fee = get_item_fee

    @classmethod
    def from_rule_name(cls, rule_name: str, get_item_fee: Callable, intraday_sep=' ', interday_sep='_'):
        days = []
        for day in rule_name.split(interday_sep):
            items = day.split(intraday_sep)
            days.append(items)

        return SequenceGraph(rule_name, get_item_fee, *days)

    def check_distance(self, other):
        possible_alignments = abs(self.n_days - other.n_days) + 1
        larger = self.sequence if self.n_days >= other.n_days else other.sequence
        larger_sequence_items_per_day = [sum(x.values()) for x in larger]
        smaller = self.sequence if self.n_days < other.n_days else other.sequence
        min_distance = float('Inf')
        for offset in range(possible_alignments):
            n_differences = 0
            for i, day in enumerate(smaller):
                check = larger[offset + i]
                for item in set(day.keys()).union(set(check.keys())):
                    check_count = check.get(item, 0)
                    day_count = day.get(item, 0)
                    item_day_diff = abs(day_count - check_count)
                    n_differences += item_day_diff

            for i in range(offset):
                n_differences += larger_sequence_items_per_day[i]

            for i in range(len(smaller) + offset, len(larger)):
                n_differences += larger_sequence_items_per_day[i]

            min_distance = n_differences if n_differences < min_distance else min_distance

        return min_distance

    def _get_left_right_differing_item(self, other):
        # note assumptions handled in higher-level function
        left_diffs = []
        right_diffs = []
        for i, day in enumerate(other.sequence):
            day = set(day.keys())
            check = set(self.sequence[i].keys())
            left_diff = check - day
            right_diff = day - check
            for item in left_diff:
                left_diffs.append((i, item))

            for item in right_diff:
                right_diffs.append((i, item))

        assert len(left_diffs) == 1
        assert len(right_diffs) == 1

        return left_diffs[0], right_diffs[0]

    def _get_extra_item(self, parent):
        diffs = []
        additional_days = self.n_days - parent.n_days
        if not additional_days:
            for i, day in enumerate(self.sequence):
                if len(day) != len(parent.sequence[i]):
                    for item, count in day.items():
                        diff = count - parent.sequence[i].get(item, 0)
                        if diff:
                            diffs.append(tuple([i, item]))

            return diffs

        additional_items = self.total_items - parent.total_items
        indices = range(self.n_days)
        indices_set = set(indices)
        for subs in combinations(indices, parent.n_days):
            partial = []
            missing = indices_set - set(subs)
            for idx in missing:
                day = self.sequence[idx]
                for item, count in day.items():
                    for n in range(count):
                        partial.append(tuple([idx, item]))

            for idx in range(parent.n_days):
                day = self.sequence[subs[idx]]
                for item, count in day.items():
                    diff = count - parent.sequence[idx].get(item, 0)
                    if diff:
                        for n in range(diff):
                            partial.append(tuple([idx, item]))

            if len(partial) == additional_items:
                diffs.append(partial)

        if len(diffs) != 1:
            # check if all flagged items are the same, except for day differences due to multiple alignments
            same = True
            for x, y in combinations(diffs, 2):
                y = sorted(y, key=lambda x: x[1])
                for i, tup in enumerate(sorted(x, key=lambda x: x[1])):
                    if tup[1] != y[i][1]:
                        same = False
                        break
                else:
                    continue
                break

            if not same:
                raise ValueError("Multiple possible alignments of parent rule with child rule")

        return sorted(diffs[0], key=lambda x: x[0])

    def rule_day_is_subset(self, n, day):
        sequence_day_counts = {}
        for item in day.split(' '):
            sequence_day_counts[item] = sequence_day_counts.get(item, 0) + 1

        rule_day_counts = self.sequence[n]
        items_to_check = set(sequence_day_counts.keys()).union(set(rule_day_counts.keys()))
        for item in items_to_check:
            sequence_count = sequence_day_counts.get(item, 0)
            rule_count = rule_day_counts.get(item, 0)
            if rule_count > sequence_count:
                return False

        return True

    @classmethod
    def is_one_child(cls, child, parent):
        if child.total_items - parent.total_items == 1:
            day_diff = child.n_days - parent.n_days
            if day_diff == 1 or day_diff == 0:
                if parent.check_distance(child) == 1:
                    return True

        return False

    def find_parent_rule(self, rule_names_by_length, sequence_graphs, rule_frequencies, current_frequency):
        subs_rule = ""
        unusual_items = [(i, x) for i, day in enumerate(self.sequence) for x in day]
        test_rules = [self.name]
        while True:
            try:
                one_smaller_rules = rule_names_by_length[sequence_graphs[test_rules[0]].total_items - 1]
            except KeyError:
                one_smaller_rules = False

            parent_q3 = []
            available_parents = []
            if one_smaller_rules:
                parent_rules = [x for x in one_smaller_rules if any(self.is_one_child(sequence_graphs[y], sequence_graphs[x]) for y in test_rules)]
                if not parent_rules:
                    break

                for x in parent_rules:
                    quants = rule_frequencies[x]
                    other_outlying = quants["75"] + 3 * (quants["75"]- quants["25"])
                    if current_frequency < other_outlying:
                        available_parents.append(x)
                        parent_q3.append(other_outlying)
            else:
                break

            if parent_q3:
                parent_rule_idx = parent_q3.index(max(parent_q3))
                subs_rule = available_parents[parent_rule_idx]
                unusual_items = sequence_graphs[self.name]._get_extra_item(sequence_graphs[subs_rule])
                break

            test_rules = parent_rules

        return (subs_rule, unusual_items)

    def find_substitute_items(self, rule_names_by_length, sequence_graphs, current_frequency, rule_frequencies, rule_ontologies):
        unusual_item_codes = []
        unusual_item_positions = []
        unusual_item_costs = []
        try:
            same_size_rules = rule_names_by_length[self.total_items]
        except KeyError:
            same_size_rules = []

        possible_substitute_rules = []
        frequencies = []
        for rule_name in same_size_rules:
            if rule_name == self.name:
                continue

            other_graph = sequence_graphs[rule_name]
            if rule_ontologies[self.name] == rule_ontologies[other_graph.name]:
                if self.n_days == other_graph.n_days:
                    if all(len(day) == len(other_graph.sequence[i]) for i, day in enumerate(self.sequence)):
                        quants = rule_frequencies[other_graph.name]
                        other_outlying = quants["75"] + 3 * (quants["75"]- quants["25"])
                        if current_frequency < other_outlying:
                            distance = self.check_distance(other_graph)
                            if distance == 2:
                                possible_substitute_rules.append(rule_name)
                                frequencies.append(other_outlying)

        ret = []
        subs_rule = ""
        if possible_substitute_rules:
            subs_rule_idx = frequencies.index(max(frequencies))
            subs_rule = possible_substitute_rules[subs_rule_idx]
            left_item, right_item = self._get_left_right_differing_item(sequence_graphs[subs_rule])
            unusual_item = left_item[1]
            replaced_item = right_item[1]
            cost = max(self.get_item_fee(unusual_item)[0] - self.get_item_fee(replaced_item)[0], 0)
            ret = [(left_item[0], left_item[1], cost)]

        return (subs_rule, ret)

    def find_overclaimed_item_for_provider(self, provider, provider_frequency=None, rule_names_by_length=None, sequence_graphs=None, rule_quantiles=None, rule_ontologies=None):
        if any(x is None for x in [provider_frequency, rule_names_by_length, sequence_graphs, rule_quantiles, rule_ontologies]):
            ret = self.replacement_rule.get(provider, False)
            if ret:
                return ret

            raise ValueError("Optional arguments must be passed if overclaimed items have not been previously found")

        ret = self.find_substitute_items(rule_names_by_length, sequence_graphs, provider_frequency, rule_quantiles, rule_ontologies)
        if not ret[1]:
            if self.total_items == 1:
                ret = ("", [(0, x, self.get_item_fee(x)[0]) for x in self.sequence[0]])
            else:
                subs_rule, sus_items = self.find_parent_rule(rule_names_by_length, sequence_graphs, rule_quantiles, provider_frequency)
                ret = (subs_rule, [(x[0], x[1], self.get_item_fee(x[1])[0]) for x in sus_items])

        self.replacement_rule[provider] = ret
        self.unusual_positions = set(x[0] for x in ret[1])

        return ret



