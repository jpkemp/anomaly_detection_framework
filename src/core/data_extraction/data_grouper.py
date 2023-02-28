'''class for holding MBS data in logical groups'''
class DataGrouper:
    '''groups data'''
    def __init__(self,
                 logger,
                 test_data,
                 basket_header,
                 group_header,
                 sub_group_header=None):
        if logger is None:
            self.log = self.mock_log
        else:
            self.log = logger.log

        self.data = test_data
        self.basket_header = basket_header
        self.group_header = group_header
        self.sub_group_header = sub_group_header
        self.create_groups()

    def mock_log(self, message):
        '''log to nowhere'''

    def create_groups(self):
        '''Create groups and subgroups from data'''
        self.group_data = self.data.groupby(self.group_header)
        if self.sub_group_header is not None:
            subgroup_data = []
            for name, group in self.group_data:
                new_groups = group.groupby(self.sub_group_header)
                for sub_name, new_group in new_groups:
                    subgroup_data.append((f"{name}__{sub_name}", new_group))

            self.subgroup_data = subgroup_data
        else:
            self.subgroup_data = None

    def create_documents(self, use_subgroups=None, explicit_1_items=True):
        '''Create documents/sentences/transactions from data'''
        if use_subgroups is None:
            if self.sub_group_header is None:
                use_subgroups = False
            else:
                use_subgroups = True

        if use_subgroups:
            data = self.subgroup_data
        else:
            data = self.group_data

        def process_group(group):
            items = group[self.basket_header].unique().tolist()
            items = [str(item) for item in items]
            if explicit_1_items and len(items) == 1:
                items.append("No other items")

            return items

        documents = [process_group(group) for _, group in data]

        return documents

    def update_properties(self, basket_header, group_header, sub_group_header):
        '''Change class properties'''
        self.basket_header = basket_header
        self.group_header = group_header
        self.sub_group_header = sub_group_header
        self.create_groups()
