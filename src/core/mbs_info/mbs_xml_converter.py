from pathlib import Path
import pickle
import xml.etree.ElementTree as ET


def convert_xml(x, year):
    path = Path(__file__).parent
    tree = ET.parse(f"{path}/{x}")
    root = tree.getroot()
    mbs = {}
    for child in root:
        item = child[0].text
        if child[1].text is not None:
            item = item + '_' + child[1].text
        mbs[item] = {}
        for i in range(2, len(child)):
            key = child[i].tag
            val = child[i].text
            mbs[item][key] = val

    with open(f'{path}/MBS_{year}.pkl', 'wb') as f:
        pickle.dump(mbs, f, pickle.HIGHEST_PROTOCOL)

def convert_groups_txt():
    cats = {}
    with open(f'{path}/mbs_groups.txt') as f:
        current_cat = ''
        current_group = ''
        while True:
            x = f.readline()
            if x is None or len(x) == 0:
                break

            x = x.split(' ')

            key = x[1].replace(':', '').replace('.', '')
            val = ' '.join(x[2:]).replace('\n', '').strip()
            if x[0][0] == 'C':
                cats[key] = {"Label":val, "Groups": {}}
                current_cat = key
            elif x[0][0] == 'G':
                cats[current_cat]["Groups"][key] = {"Label": val, "SubGroups": {}}
                current_group = key
            elif x[0][0] == 'S':
                cats[current_cat]["Groups"][current_group]["SubGroups"][key] = val

    with open(f'utilities/mbs_groups.pkl', 'wb') as f:
        pickle.dump(cats, f, pickle.HIGHEST_PROTOCOL)

if __name__ == '__main__':
    filename = 'MBS.XML-211222.XML'
    year = '2021'
    convert_xml(filename, year)
    # convert_groups_txt()