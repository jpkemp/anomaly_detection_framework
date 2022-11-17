import pandas as pd
from src.core.algorithms.sequence.sequence import SequentialPatternDetection as SPD

class ProviderCourseRules:
    def __init__(self, provider_id, context, courses, args):
        self.n_courses = len(courses)
        self.courses = courses
        self.id = provider_id
        self.context = context

        sequences = [x.item_sequence.sequence for x in courses]
        filename= f"{provider_id}_{context}"
        result = SPD.mine_spam(sequences, args, filename)
        result.index = result['pattern'].apply(lambda x: '_'.join(x))
        self.rules = result.index
        self.replaced_rules = {}
        self.proportion = result['sup'].apply(lambda x: x / self.n_courses)
        if args[-1]:
            self.rule_to_course = {x: set(y) for x, y in result['sid'].to_dict().items()}

    def get_proportional_rule_occurrence(self, rule):
        try:
            return self.proportion.loc[rule]
        except KeyError:
            return 0
