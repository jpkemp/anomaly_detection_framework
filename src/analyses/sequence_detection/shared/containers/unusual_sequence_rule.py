class UnusualSequenceRule:
    def __init__(self, rule, quantiles, ontology_converter, cost_converter):
        self.rule = rule
        self.ontology, self.cost = self._parse_items(rule, ontology_converter, cost_converter)
        self.quantiles = quantiles
        self.provider_order = []
        self.rates = []
        self.diffs = []
        self.occurrences = 0.0

    def _parse_items(self, rule, ontology_converter, cost_converter):
        loc = set()
        cost = 0
        itemset = rule.split(' ')
        for items in itemset:
            for item in items.split('_'):
                ont = ontology_converter(item)
                loc.add(ont)
                cost += cost_converter(item)[0]

        ontology = '_'.join(sorted(loc))

        return ontology, cost

    def add_provider(self, provider_id, rate, provider_courses):
        self.provider_order.append(provider_id)
        self.rates.append(rate)
        self.diffs.append(rate - self.quantiles["50"])
        self.occurrences += rate * provider_courses