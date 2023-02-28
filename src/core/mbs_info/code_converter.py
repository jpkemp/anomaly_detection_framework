'''Code converter class for PBS items and MBS RSP codes'''
import re
import pickle
import pandas as pd
from pathlib import Path

class CodeConverter:
    '''Converter for PBS items and MBS RSP codes'''
    def __init__(self, year):
        year = str(year)
        available_years = ['2014', '2019', '2021']
        if year not in available_years:
            year = '2019'

        self.year = year

        converter_path = Path(__file__).parent
        mbs_group_filename = converter_path / 'updated_group_info.pkl'
        mbs_item_filename = converter_path / f'MBS_{year}.pkl'
        rsp_filename = converter_path / 'SPR_RSP.csv'
        pbs_item_filename = converter_path / 'pbs_item_drug_map_2022.csv'
        pbs_atc_filename = converter_path / 'atc_codes.pqt'

        with open(mbs_item_filename, 'rb') as f:
            self.mbs_item_dict = pickle.load(f)

        with open(mbs_group_filename, 'rb') as f:
            self.mbs_groups_dict = pickle.load(f)

        self.rsp_table = pd.read_csv(rsp_filename)
        self.valid_rsp_num_values = self.rsp_table['SPR_RSP'].unique()
        self.valid_rsp_str_values = self.rsp_table['Label'].unique()

    def convert_mbs_category_number_to_label(self, cat_num):
        '''Returns a category label'''
        cat_num = str(cat_num)
        try:
            x = self.mbs_groups_dict[cat_num]["Label"]
        except KeyError:
            x = 'Item not in dictionary'

        return x

    def convert_mbs_code_to_description(self, code):
        '''Returns the description of an MBS item'''
        item = self.mbs_item_dict.get(str(int(code)), None)
        if item is None:
            return f"Item code {code} not in {self.year} dictionary"

        return f"{item['Description']}"

    def convert_mbs_code_to_group_labels(self, code):
        '''Returns the group description of an MBS item'''
        item = self.mbs_item_dict.get(str(int(code)), None)
        if item is None:
            return [f"Item code {code} not in {self.year} dictionary"]

        cat = item['Category']
        group = item['Group']
        sub = item['SubGroup']
        head = item['SubHeading']

        cat_desc = self.mbs_groups_dict[cat]["Label"]
        group_desc = self.mbs_groups_dict[cat][group]["Label"]
        try:
            sub_desc = self.mbs_groups_dict[cat][group][sub]["Label"]
        except KeyError:
            sub_desc = None

        try:
            head_desc = self.mbs_groups_dict[cat][group][sub][head]["Label"]
        except KeyError:
            head_desc = None

        if sub_desc is None:
            if head_desc is None:
                return [cat_desc, group_desc]

            return [cat_desc, group_desc, None, sub_desc]



        if head_desc is None:
            return [cat_desc, group_desc, sub_desc]

        return [cat_desc, group_desc, sub_desc, head_desc]

    def convert_mbs_code_to_group_numbers(self, code):
        '''convert mbs item code number to category definition'''
        item = self.mbs_item_dict.get(str(int(code)), None)
        if item is None:
            return [f"Item code {code} not in {self.year} dictionary"]

        return [item['Category'], item['Group'], item['SubGroup'], item['SubHeading']]

    def convert_mbs_code_to_ontology_label(self, code):
        group = self.convert_mbs_code_to_group_numbers(code)
        label = '_'.join(['None' if x is None else x for x in group])

        return label

    def convert_rsp_num(self, rsp):
        '''convert RSP number to string'''
        if int(rsp) not in self.valid_rsp_num_values:
            raise ValueError(f"{rsp} is not a valid SPR_RSP")

        return self.rsp_table.loc[self.rsp_table['SPR_RSP'] == int(rsp)]['Label'].values.tolist()[0]

    def convert_rsp_str(self, rsp):
        '''convert RSP string to number'''
        if str(rsp) not in self.valid_rsp_str_values:
            raise ValueError(f"{rsp} is not a valid name")

        return self.rsp_table.loc[self.rsp_table['Label'] == str(rsp)]['SPR_RSP'].values.tolist()[0]

    def convert_state_num(self, state):
        '''Convert a state number to human readable'''
        state_id = str(state)
        state_names = {
            '1': 'ACT + NSW',
            '2': 'VIC + TAS',
            '3': 'NT + SA',
            '4': 'QLD',
            '5': 'WA'
        }

        return state_names.get(state_id, "Not a valid state")

    def get_mbs_item_fee(self, code):
        '''Return the fee amount and type for an MBS item'''
        item = self.mbs_item_dict.get(str(int(code)), None)
        if item is None:
            return 500, "Not in dictionary"

        fee_type = "ScheduleFee"
        if "ScheduleFee" not in item:
            derived_fee = item["DerivedFee"]
            fee_type = "DerivedFee"
            try:
                number = re.search(r'item\s(\d+)', derived_fee)[1]
            except TypeError:
                if code == '51303':
                    return 113, fee_type
                elif code == '31340' or code == '44376':
                    return 544.43, fee_type
                else:
                    try:
                        return float(re.search(r'\$(\d+\.\d+)', derived_fee)[1]), fee_type
                    except TypeError as e:
                        raise KeyError(f"{code} does not have an easily accessible fee") from e

            item = self.mbs_item_dict.get(str(number), None)

        dollar_fee = item["ScheduleFee"]
        fee = float(dollar_fee)

        return fee, fee_type

    def get_mbs_items_in_category(self, cat_no):
        return [x for x, y in self.mbs_item_dict.items() if y["Category"] == str(cat_no)]

    def get_mbs_items_in_group(self, cat_no, group_id):
        return [x for x, y in self.mbs_item_dict.items() if (y["Category"] == str(cat_no) and y["Group"] == group_id)]

    def get_mbs_items_in_subgroup(self, cat_no, group_id, subgroup_no):
        return [x for x, y in self.mbs_item_dict.items() if (y["Category"] == str(cat_no) and y["Group"] == group_id and y["SubGroup"] == str(subgroup_no))]

    def get_mbs_items_in_subheading(self, cat_no, group_id: str, subgroup_no, subheading_no):
        subgroup_no = str(subgroup_no) if subgroup_no is not None else None
        subheading_no = str(subheading_no) if subheading_no is not None else None
        return [x for x, y in self.mbs_item_dict.items() if (y["Category"] == str(cat_no)
                                                             and y["Group"] == group_id
                                                             and y["SubGroup"] == subgroup_no
                                                             and y["SubHeading"] == subheading_no)]

    def get_mbs_code_as_line(self, code):
        '''Get MBS item code information as a string formatted for printing'''
        groups = self.convert_mbs_code_to_group_labels(code)
        desc = self.convert_mbs_code_to_description(code)
        mod_line = [f'"{x}"' for x in groups]
        if len(mod_line) == 2:
            mod_line.append('')

        mod_line.append(str(int(code)))
        mod_line.append(f'"{desc}"')

        return mod_line

    def write_mbs_codes_to_csv(self, codes, filename, additional_cols=None, additional_headers=None):
        '''Get MBS item code information and write to a file'''
        with open(filename, 'w+') as f:
            header = "Group,Category,Sub-Category,Item,Description,Cost,FeeType"
            if additional_cols is not None:
                for col in additional_cols:
                    assert len(col) == len(codes)

                if additional_headers:
                    for aheader in additional_headers:
                        header += f",{aheader}"

            header += "\r\n"
            f.write(header)
            for idx, code in enumerate(codes):
                mod_line = self.get_mbs_code_as_line(code)
                item_cost, fee_type = self.get_mbs_item_fee(code)
                item_cost = "${:.2f}".format(item_cost)
                line = ','.join(mod_line) + f',{item_cost},{fee_type}'
                if additional_cols is not None:
                    for col in additional_cols:
                        line += f",{col[idx]}"

                line += '\r\n'
                f.write(line)
