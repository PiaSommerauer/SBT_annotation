import glob
import csv
import os
from collections import defaultdict


def load_replacement_info():

    prop_dict = defaultdict(dict)
    path = '../data_pair_filtering/concept-replacement/*.csv'
    header = ['property', 'lemma', 'label', 'certainty', 'sources_str']
    for f in glob.glob(path):
        basename = os.path.basename(f)
        p, status = basename.split('.')[0].split('-')
        prop_dict[p][status] = dict()
        with open(f) as infile:
            data_dict_list = csv.DictReader(infile, delimiter = '\t', fieldnames = header)
            for d in data_dict_list:
                pair = (p, d['lemma'])
                prop_dict[p][status][pair] = d
    return prop_dict




def load_original_dataset():
    collections = ['perceptual', 'activities', 'complex', 'parts']
    prop_dict = defaultdict(dict)
    for col in collections:
        path = f'../data/original/{col}.csv'
        with open(path) as infile:
            data = csv.DictReader(infile, delimiter=',')
            for d in data:
                d['collection'] = col
                p = d['property']
                pair = (p,  d['lemma'])
                prop_dict[p][pair] = d
    return prop_dict


def replace_data(prop_dict_replacements, prop_dict_original):
    data_replaced = defaultdict(list)
    for prop, replacement_dict in prop_dict_replacements.items():
        # get original data for the property:
        original_set_dict = prop_dict_original[prop]
        print(prop)
        print(len(original_set_dict))
        # get original data - excluded concepts:
        replacement_excluded = replacement_dict['excluded']
        keep = [d for pair, d in original_set_dict.items() if pair not in replacement_excluded]
        collection = keep[0]['collection']
        [d.pop('collection') for d in keep]
        print('to keep')
        print(len(keep))
        # add replacements:
        [keep.append(d) for p, d in replacement_dict['replacement'].items()]
        print('to keep + replacements')
        print(len(keep))
        data_replaced[collection].extend(keep)
    return data_replaced

def data_to_files(data_replaced):

    for collection, data in data_replaced.items():
        path = f'../data/resampled/{collection}.csv'
        header = data[0].keys()
        with open(path, 'w') as outfile:
            writer = csv.DictWriter(outfile, fieldnames = header, delimiter = ',')
            writer.writeheader()
            for d in data:
                writer.writerow(d)

def main():
    prop_dict_replacements = load_replacement_info()
    prop_dict_original = load_original_dataset()
    data_replaced = replace_data(prop_dict_replacements, prop_dict_original)
    data_to_files(data_replaced)









if __name__ == '__main__':
    main()