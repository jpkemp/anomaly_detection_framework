'''Functions for colouring and converting graph nodes by MBS information'''
from src.core.algorithms.graphs.graph_utils import GraphUtils
from src.core.io import config as hc

class MbsGraphColouring(GraphUtils):
    '''Functions for colouring graph nodes by MBS information'''
    def __init__(self, logger, code_converter):
        super().__init__(logger)
        self.code_converter = code_converter
        self.log = logger.log

    def color_providers(self, d, data, colour_keys=True, colour_vals=True):
        '''colour nodes based on MBS SPR_RSP'''
        def get_provider_val(spr):
            spr = int(spr)
            rows = data[data[hc.PR_ID] == spr]
            rsps = rows[hc.PR_SP].mode().tolist()
            if len(rsps) == 1:
                rsp = rsps[0]
            else:
                rsp = 'Multiple'

            return rsp

        lookup = {}
        for k in d.keys():
            lookup[k] = get_provider_val(k)

        used_colors = set()
        for k, v in d.items():
            if colour_keys:
                if lookup[k] not in lookup:
                    color = get_provider_val(k)
                    lookup[k] = color
                    used_colors.add(color)
            if colour_vals:
                for key in v.keys():
                    if key not in lookup:
                        color = get_provider_val(key)
                        lookup[key] = color
                        used_colors.add(color)

        colour_table = {}
        for i, col in enumerate(used_colors):
            color = int(i * 255 / len(used_colors))
            anti_col = 255 - color
            # g = int(min(color, anti_col)/2)
            c = '{:02x}'.format(color)
            a = '{:02x}'.format(anti_col)

            colour_table[str(col)] = {'color': f"#{a}{c}{0}"}

        colors = {}
        for k, v in lookup.items():
            colors[str(k)] = colour_table[str(v)]

        return colors, colour_table

    def colour_mbs_codes(self, d):
        '''colour nodes based on MBS item groups'''
        get_color = {
            'I': 'red', # item not in dictionary. Colours: https://serialmentor.com/dataviz/color-pitfalls.html
            '1': '#E69F00',
            '2': '#56B4E9',
            '3': '#009E73',
            '4': '#F0E442',
            '5': '#0072B2',
            '6': '#D55E00',
            '7': '#CC79A7',
            '8': '#ffd912'
        }

        all_items = self.flatten_graph_dict(d)
        attrs = {}
        color_map = set()
        for item in all_items:
            if item == "No other items":
                group_no = 'I'
            else:
                group_no = self.code_converter.convert_mbs_code_to_group_numbers(item)[0]

            color = get_color[group_no]
            attrs[item] = {'color': color}
            color_map.add(group_no)

        legend = {}
        for color in color_map:
            color_name = get_color[color]
            color_label = self.code_converter.convert_mbs_category_number_to_label(color)
            legend[color_name] = {'color': color_name,
                                  'label': color_label.replace(' ', '\n'),
                                  'labeljust': ';', 'rank': 'max'}

        return (d, attrs, legend)

    def convert_graph_and_attrs(self, d, header, test_data=None):
        '''convert code information to human-readable within a graph'''
        attrs = None
        legend = None
        if header == hc.PR_SP:
            self.log("Converting RSP codes")
            converted_d = self.convert_rsp_keys(d)
        elif header == hc.ITEM:
            self.log("Converting MBS codes")
            (converted_d, attrs, legend) = self.convert_mbs_codes(d)
        elif header == hc.PR_ID:
            self.log("Colouring providers")
            if test_data is None:
                raise RuntimeError("Test data must be specified when header is SPR")
            converted_d = d
            attrs, legend = self.color_providers(converted_d, test_data)
        else:
            converted_d = d

        return converted_d, attrs, legend

    def convert_mbs_codes(self, d, attrs=None):
        '''change node text from MBS item codes to human readable descriptions'''
        get_color = {
            'I': 'red', # for item not in dictionary
            '1': '#E69F00',
            '2': '#56B4E9',
            '3': '#009E73',
            '4': '#F0E442',
            '5': '#0072B2',
            '6': '#D55E00',
            '7': '#CC79A7',
            '8': '#ffd912'
        }

        lookup = {}
        for k in d.keys():
            if k == "No other items":
                lookup["No other items"] = "No other items"
            else:
                labels = self.code_converter.convert_mbs_code_to_group_labels(k)
                lookup[k] = '\n'.join(labels)

        new_data = {}
        colors = {}
        color_map = set()
        for k, v in d.items():
            new_k = f'{lookup[k]}\n{k}'
            if new_k not in new_data:
                if new_k == "No other items" or new_k == "No other items\nNo other items":
                    group_no = 'I'
                else:
                    group_no = self.code_converter.convert_mbs_code_to_group_numbers(k)[0]

                color = get_color[group_no]
                colors[new_k] = {'color': color}
                if attrs is not None and k in attrs:
                    colors[new_k] = {**attrs[k], **colors[new_k]}

                color_map.add(group_no)
                new_data[new_k] = {}
            for key, val in v.items():
                if key not in lookup:
                    if k == "No other items":
                        lookup["No other items"] = "No other items"
                    else:
                        labels = self.code_converter.convert_mbs_code_to_group_labels(key)
                        lookup[key] = '\n'.join(labels)

                new_key = f'{lookup[key]}\n{key}'
                new_data[new_k][new_key] = val

                if key not in d:
                    if new_key == "No other items" or new_key == "No other items\nNo other items":
                        group_no = 'I'
                    else:
                        group_no = self.code_converter.convert_mbs_code_to_group_numbers(key)[0]

                    color = get_color[group_no]
                    colors[new_key] = {'color': color}
                    if attrs is not None and key in attrs:
                        colors[new_key] = {**attrs[key], **colors[new_key]}

                    color_map.add(group_no)

        legend = {}
        for color in color_map:
            color_name = get_color[color]
            color_label = self.code_converter.convert_mbs_category_number_to_label(color)
            legend[color_name] = {'color': color_name,
                                  'label': color_label.replace(' ', '\n'),
                                  'labeljust': ';',
                                  'rank': 'max'}

        return (new_data, colors, legend)

    def convert_rsp_keys(self, d):
        '''convert node text from SPR_RSP numbers to human readable text'''
        lookup = {}
        for k in d.keys():
            if k == "No other items":
                lookup["No other items"] = "No other items"
            else:
                lookup[k] = self.code_converter.convert_rsp_num(k)

        new_data = {}
        for k, v in d.items():
            if lookup[k] not in new_data:
                new_data[lookup[k]] = {}
            for key, val in v.items():
                if key not in lookup:
                    if key == "No other items":
                        lookup["No other items"] = "No other items"
                    else:
                        lookup[key] = self.code_converter.convert_rsp_num(key)

                new_data[lookup[k]][lookup[key]] = val

        return new_data
