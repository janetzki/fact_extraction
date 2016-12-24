from tqdm import tqdm
import csv

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
                if name in self.types:
                    self.types[name].append(inst_type)
                else:
                    self.types[name] = []

    def fromEntity(name):
        if name in self.types:
            return self.types[name]
        else:
            return []

    def fromEntities(entities):
        types = []
        for entity in entities:
            types.extend(self.fromEntity(entity))
        return types