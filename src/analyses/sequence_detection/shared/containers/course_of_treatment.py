'''classes for holding extracted patient and episode information'''
from src.core.algorithms.sequence.format import FormatSpmf
import src.core.io.config as hc

class CourseOfTreatment:
    '''container for extracted episode information'''
    def __init__(self, start, end, data, identifier, providers, context, patient_id):
        self.start = start
        self.end = end
        self.item_sequence = FormatSpmf.construct_sequence(data, identifier)
        self.ontology_sequence = FormatSpmf.construct_sequence(data, identifier, item_id="Ontology_cat")
        self.involved_providers = providers
        self.cost = data[hc.COST].sum()
        self.item_costs = data.groupby(hc.ITEM).agg({hc.COST: 'sum'}).to_dict()[hc.COST]
        self.context = context
        self.patient_id = patient_id

class ExtendedCourse:
    def __init__(self, course):
        self.course = course
        self.flagged_timestamps = set()
        self.double_flagged_timestamps = set()
        self.rules = set()
        self.flagged_service_frequencies = dict()
        self.course_position_costs = dict()
        self.position_items = dict()
        self.replaced_rules = dict()
        self.item_costs = dict()

    def sum_costs_at_position(self, position):
        return sum(x for x in self.course_position_costs[position].values())

    def update_flagged_position(self, position, unusual):
        item = unusual[1]
        cost = unusual[2]
        self.double_flagged_timestamps.add(position)
        current_items = self.position_items.get(position, set())
        current_costs = self.course_position_costs.get(position, 0)
        if item not in current_items:
            current_costs += cost
            current_items.add(item)
            total_costs = self.item_costs.get(item, 0)
            total_costs += cost
            self.item_costs[item] = total_costs

        self.position_items[position] = current_items
        self.course_position_costs[position] = current_costs

    def update_course_flags(self, provider, graph, end):
        end += 1
        unusual_items = graph.find_overclaimed_item_for_provider(provider)
        start = end - graph.n_days
        self.rules.add(graph.name)
        positions =  graph.unusual_positions

        for i in range(0, end - start):
            self.flagged_timestamps.add(start + i)
            if i in positions:
                updates = [x for x in unusual_items[1] if x[0] == i]
                for update in updates:
                    self.update_flagged_position(start + i, update)

    def get_unusual_course_costs(self):
        return sum(x for x in self.course_position_costs.values())

    def label_rare_items(self, rare_items, rare_item_costs):
        for i, day in enumerate(self.course.item_sequence.sequence):
            items = day.split(' ')
            for item in items:
                if item in rare_items:
                    self.flagged_timestamps.add(i)
                    unusual = tuple([i, item, rare_item_costs[item]])
                    self.update_flagged_position(i, unusual)

    def process_sequence_graph(self, provider, graph):
        partial_sequences = {n: 0 for n in range(graph.n_days)}
        for i, day in enumerate(self.course.item_sequence.sequence):
            for j in partial_sequences:
                if not graph.rule_day_is_subset(partial_sequences[j], day):
                    partial_sequences[j] = -1

            if partial_sequences[0] == graph.n_days - 1:
                self.update_course_flags(provider, graph, i)
            for j in range(1, graph.n_days):
                partial_sequences[j - 1] = partial_sequences[j] +1

            partial_sequences[graph.n_days - 1] = 0


