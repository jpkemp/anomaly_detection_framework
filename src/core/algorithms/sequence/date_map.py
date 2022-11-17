'''create date map from pandas date series'''
from datetime import timedelta
import pandas as pd

class DateMap:
    def __init__(self, dates):
        sorted_unique = pd.Series(dates.unique()).sort_values()
        start = sorted_unique.min()
        date_map = {}
        for date in sorted_unique:
            days = date - start
            date_map[date] = (days + timedelta(days=1)).days

        self.map = date_map
        self.reversed_map = {v: k for k, v in date_map.items()}

    def get_date_from_timestamp(self, timestamp):
        return self.reversed_map[timestamp]

    def get_timestamp_from_date(self, date):
        return self.map[date]