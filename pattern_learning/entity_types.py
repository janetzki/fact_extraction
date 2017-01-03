from tqdm import tqdm
import csv
from collections import Counter

delimiter = '#'
total_lines = 3260000  # TODO: replace magic number with line counter


class InstanceTypes(object):
    def __init__(self, types_path='../data/types_en.csv'):
        self.types = {}

        print('\n\nReading types file...')
        with open(types_path, 'r') as fin:
            next(fin)

            reader = csv.reader(fin, delimiter=delimiter)
            for name, inst_type in tqdm(reader, total=total_lines):
                self.types.setdefault(name, []).append(inst_type)

    def from_entity(self, name):
        if name in self.types:
            return Counter(self.types[name])
        else:
            return Counter()
