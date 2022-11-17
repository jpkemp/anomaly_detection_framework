'''Custom algorithms for detecting sequential patterns'''
import os
from datetime import datetime
from itertools import combinations
from random import randint
from spmf import Spmf
from src.core.algorithms.sequence.format import FormatSpmf

class SequentialPatternDetection:
    '''Container for sequential pattern detection algorithms'''
    @classmethod
    def check_overlap(cls, x0, x1, y0, y1, tol=0):
        if max(x0, y0) > (min(x1, y1) + tol):
            return False
        else:
            return True

    @classmethod
    def generate_file_name(cls):
        rand = randint(100000,999999)
        temp_file = f"spmf_output_{datetime.now().isoformat()}_{rand}"

        return temp_file

    @classmethod
    def remove_non_maximal_patterns(cls, patterns, timestamps=None):
        drop_indices = []
        supersets = [x for x in patterns if len(x) > 1]
        if supersets:
            for i, p in enumerate(patterns):
                for s in supersets:
                    if p < s: # For sets < checks if proper subset
                        drop_indices.append(i)
                        break

        for i in reversed(drop_indices):
            del patterns[i]
            if timestamps is not None:
                del timestamps[i]

    @classmethod
    def combine_overlapping_timestamped_patterns(cls, patterns, timestamps, tolerance=0):
        '''first combine timestamps, then get patterns within those timestamps
           expects a list of 2-tuples'''
        patterns = [set(x) for x in patterns]
        if len(patterns) >= 1:
            timestamps, patterns = (list(t) for t in zip(*sorted(zip(timestamps, patterns))))
        if len(patterns) > 1:
            reduced_stamps = [list(timestamps[0])]
            reduced_patterns = [patterns[0]]
            for i, current in enumerate(timestamps[1:]):
                idx = i + 1
                previous = reduced_stamps[-1]
                if cls.check_overlap(previous[0], previous[1], current[0], current[1], tol=tolerance):
                    previous[1] = max(current[1], previous[1])
                    reduced_patterns[-1].update(patterns[idx])
                else:
                    reduced_stamps.append(list(current))
                    reduced_patterns.append(patterns[idx])
        else:
            reduced_patterns = patterns
            reduced_stamps = timestamps

        return [tuple(sorted(x)) for x in reduced_patterns], [tuple(x) for x in reduced_stamps]

    @classmethod
    def mine_local_periodic_patterns(cls, sequence, timestamps, max_period, min_duration, max_spill, algorithm="LPPGrowth"):
            lines = FormatSpmf.convert_to_spmf_episode(sequence, timestamps)
            temp_file = cls.generate_file_name()
            pattern_miner = Spmf(algorithm,
                                    input_direct=lines,
                                    output_filename=temp_file,
                                    arguments=[max_period, min_duration, max_spill, False])
            pattern_miner.run()
            patterns, timestamps = FormatSpmf.parse_timestamped_spmf_output(pattern_miner.parse_output())
            os.remove(temp_file)

            return patterns, timestamps

    @classmethod
    def write_input_file(cls, output_file, sequences):
        input_file = f"input_{output_file}.txt"
        with open(input_file, 'w+') as f:
            f.write(sequences)

        return input_file

    @classmethod
    def mine_spam(cls, sequences, args, output_file=None, remove_output_file=True):
        if output_file is None:
            output_file = cls.generate_file_name()

        formatted_sequences = FormatSpmf.convert_to_spmf_standard(sequences)
        input_file = cls.write_input_file(output_file, formatted_sequences)
        pattern_miner = Spmf("CM-SPAM", input_filename=input_file, output_filename=output_file, arguments=args)
        pattern_miner.run()

        if args[-1]:
            df = FormatSpmf.parse_spam_with_row_occurrences(output_file)
        else:
            df = pattern_miner.to_pandas_dataframe()
            test = [tuple(x) for x in df['pattern'].values]
            q = {}
            for x in test:
                q[x] = (q.get(x, 0)) + 1
            if any(val > 1 for val in q.values()):
                x = 1

        os.remove(input_file)
        if remove_output_file:
            os.remove(output_file)

        return df
