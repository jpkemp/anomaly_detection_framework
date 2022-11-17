import src.core.io.config as hc

def get_ontology_information(data, code_converter, ontology_of_interest):
    data["Ontology"] = data[hc.ITEM].apply(lambda x: code_converter.convert_mbs_code_to_ontology_label(x)).astype("category")
    data["Ontology_cat"] = data["Ontology"].cat.codes.astype(str)
    cat_map = dict(enumerate(data['Ontology'].cat.categories))
    # self.pickle_data(cat_map, self.logger.get_file_path('cat_map.pkl'))
    ontology_of_interest_data = data[data["Ontology"].str.startswith(ontology_of_interest)]

    return ontology_of_interest_data