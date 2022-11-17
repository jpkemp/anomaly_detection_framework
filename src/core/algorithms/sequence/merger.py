from copy import deepcopy
from dataclasses import dataclass

@dataclass
class MergeParameters:
    max_period: int = None
    max_spill: int = None
    min_duration: int = None
    max_initiator_timedelta: int = None
    drop_no_initiator_courses: bool = False

class Merger:
    '''functions for merging parts of a multi-part sequence (i.e., initiator or terminator with timestamps from other patterns)'''
    @classmethod
    def merge_initiator(cls, initiator_dates, timestamps, max_interval, drop_no_initiator=True):
        '''Find relevant timestamps and merge them'''
        timestamps = deepcopy(timestamps)
        has_init = set()
        for init_date in sorted(initiator_dates):
            prior = []
            during = []
            no_subsequent = 0
            many_subsequent = 0
            for j, tup in enumerate(timestamps):
                difference_beginning = tup[0] - init_date
                difference_end = tup[1] - init_date
                if difference_beginning > 0 and difference_beginning <= max_interval:
                    prior.append(j)
                elif difference_end >= 0 and difference_beginning <=0:
                    during.append(j)

            has_init.update(prior)
            has_init.update(during)
            if not prior and not during:
                # self.log(f"{ep_id} had initiator with no following sequence")
                no_subsequent += 1
                # timestamps.append(tuple([init_date, init_date]))
            elif sum([len(prior), len(during)]) > 1:
                # self.log(f"{ep_id} had multiple valid sequences following an initiator")
                many_subsequent += 1
                idxs = set(prior + during)
                mins = min([init_date] + [timestamps[j][0] for j in idxs])
                maxs = max([init_date] + [timestamps[j][1] for j in idxs])
                for j in sorted(idxs, reverse=True):
                    del timestamps[j]
                    has_init.remove(j)

                new_timestamp = tuple([mins, maxs])
                timestamps.append(new_timestamp)
                timestamps.sort()
                has_init.add(timestamps.index(new_timestamp))
            elif prior:
                timestamps[prior[0]] = tuple([init_date, timestamps[prior[0]][1]])
            elif during:
                pass
            else:
                raise RuntimeError("This should never happen")

        # combine initiators with LPPs
        if drop_no_initiator:
            remove =  set(range(len(timestamps))) - has_init
            for j in sorted(remove, reverse=True):
                del timestamps[j]

        return timestamps
