from tqdm import tqdm
import csv
from collections import Counter

delimiter = "#"
total_lines = 3260000


class InstanceTypes(object):
    def __init__(self, types_path='../data/types_en.csv'):
        self.types = {}

        print('Reading types file...')
        with open(types_path, 'r') as file:
            next(file)

            reader = csv.reader(file, delimiter=delimiter)
            for name, inst_type in tqdm(reader, total=total_lines):
                self.types.setdefault(name, []).append(inst_type)

    def fromEntity(self, name):
        if name in self.types:
            return Counter(self.types[name])
        else:
            return Counter()