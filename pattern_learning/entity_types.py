from tqdm import tqdm
from collections import Counter
import csv
import imp

line_counting = imp.load_source('line_counting', '../helper_functions/line_counting.py')

delimiter = '#'


class InstanceTypes(object):
    def __init__(self, types_path='../data/types_en.csv', type_inheritance_path='../data/types_inheritance_en.csv'):
        self.types = {}
        self.parent_types = {}

        total_lines = line_counting.count_lines(types_path)
        print('\n\nReading types file...')
        with open(types_path, 'r') as fin:
            next(fin)

            reader = csv.reader(fin, delimiter=delimiter)
            for name, inst_type in tqdm(reader, total=total_lines):
                self.types.setdefault(name, []).append(inst_type)

        total_lines = line_counting.count_lines(type_inheritance_path)
        print('\n\nReading type inheritance file...')
        with open(type_inheritance_path, 'r') as fin:
            next(fin)
            reader = csv.reader(fin, delimiter=delimiter)
            for inst_type, parent_type in tqdm(reader, total=total_lines):
                self.parent_types[inst_type] = parent_type

    def count_types(self, name):
        counter = Counter()
        if name in self.types:
            counter = Counter(self.types[name])
        if len(counter) > 1:
            assert False
        return counter

    def get_parent_type(self, type_name):
        if type_name in self.parent_types:
            return self.parent_types[type_name]
        return False

    def get_transitive_types(self, types):
        new_types = Counter()
        for type in list(types):
            new_types[type] += 1
            parent = self.get_parent_type(type)
            while parent:
                new_types[parent] += 1
                parent = self.get_parent_type(parent)
        return new_types
