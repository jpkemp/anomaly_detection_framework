from dataclasses import dataclass
from datetime import timedelta
import pandas as pd
from src.core.algorithms.sequence.date_map import DateMap
import src.core.io.config as hc

@dataclass
class SequenceInformation:
    sequence: list
    timestamps: list
    costs: list
    identifier: str

class FormatSpmf:
    @classmethod
    def create_date_map(cls, dates):
        '''create date map from pandas date series'''
        date_map = DateMap(dates)

        return date_map

    @classmethod
    def construct_sequence(cls,
                           info,
                           identifier,
                           item_id=hc.ITEM,
                           timestamp_id=hc.DATE,
                           cost_id=hc.COST,
                           date_map=None,
                           uniques_only_in_itemset=False):
        '''convert a dataframe for a single event into sequence data'''
        ret = SequenceInformation([], [], [], identifier)
        if date_map is None:
            date_map = cls.create_date_map(info[timestamp_id])

        days = info.groupby(timestamp_id)
        for day, group in days:
            items = group[item_id].unique().tolist()
            if uniques_only_in_itemset:
                itemset = set(items)
            else:
                itemset = items

            element = ' '.join(tuple(sorted(itemset)))
            ret.sequence.append(element)
            day_costs = int(group[cost_id].sum())
            ret.costs.append(day_costs)
            ret.timestamps.append(date_map.get_timestamp_from_date(day))

        return ret

    @classmethod
    def convert_to_spmf_standard(cls, sequences):
        all_items = sorted(set([x for seq in sequences for day in seq for x in day.split(' ')]))
        cat_map = {v: str(k) for k, v in enumerate(all_items)}
        output = "@CONVERTED_FROM_TEXT\n"
        for code, n in cat_map.items():
            output += f"@ITEM={n}={code}\n"

        lines = []
        for seq in sequences:
            line = []
            for day in seq:
                par_line = []
                items = day.split(' ')
                for item in items:
                    cat = cat_map[item]
                    par_line.append(cat)

                line.append(' '.join(par_line))

            line = ' -1 '.join(line)
            lines.append(line)

        return output + ' -1 -2\n'.join(lines) + ' -1 -2\n'

    @classmethod
    def convert_to_spmf_episode(cls, sequence, dates):
        lines = []
        for i, seq in enumerate(sequence):
            line = seq + f"|{dates[i]}"
            lines.append(line)

        return '\n'.join(lines)

    @classmethod
    def parse_timestamped_spmf_output(cls, miner_patterns):
        patterns_out = []
        timestamps_out = []
        for line in miner_patterns:
            pattern, times = line[0].split(" #TIME-INTERVALS: ")
            pattern = set(pattern.split(' '))
            timestamps = times.replace(' ', '').replace('][', '\n').replace('[', '').replace(']', '').split('\n')
            for time in timestamps:
                formatted_time = tuple(int(x) for x in time.split(','))
                timestamps_out.append(formatted_time)
                patterns_out.append(pattern)

        return patterns_out, timestamps_out

    @classmethod
    def parse_spam_with_row_occurrences(cls, filename):
        records = []
        with open(filename, 'r') as f:
            for line in f:
                line = line.replace(' -2', '').replace('\n', '')
                items = line.split(' -1 ')
                rule = []
                for item in items:
                    if 'SUP' in item:
                        spl = item.split(' ')
                        support = spl[1]
                        occurrences = spl[3:]
                    else:
                        rule.append(item)

                record = (rule, support, occurrences)
                records.append(record)

            ret = pd.DataFrame.from_records(records, columns=["pattern", "sup", "sid"])
            ret["sup"] = ret["sup"].astype(int)

            return ret
