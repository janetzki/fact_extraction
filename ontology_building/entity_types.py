from tqdm import tqdm
from collections import Counter
import csv
import unicodecsv
import imp

logger = imp.load_source('logger', '../logging/logger.py')
from logger import Logger

line_counting = imp.load_source('line_counting', '../helper_functions/line_counting.py')


class EntityTypes(object):
    def __init__(self, types_paths=[], types_index='../data/yago_index.csv',
                 types_indexed_file='../data/yago_types.csv',
                 type_inheritance_path='../data/types_inheritance_en.csv'):
        self.logger = Logger.from_config_file()
        self.types = {}
        self.parent_types = {}
        self.delimiter = '#'
        self.join_character = '_'

        if types_indexed_file:
            total_lines = line_counting.cached_counter.count_lines(types_index)
            with open(types_index, 'rb') as findex:
                self.logger.print_info('Reading types index')
                reader = unicodecsv.reader(findex, delimiter=self.delimiter)
                for entity, types_info in tqdm(reader, total=total_lines):
                    for info in types_info.split(self.join_character):
                        self.types.setdefault(entity, []).append(info)

            self.types_indexed_file = open(types_indexed_file, 'rb')

        for path in types_paths:
            self._load_types(path)
        self._load_type_inheritance(type_inheritance_path)

    def __del__(self):
        if self.types_indexed_file:
            self.types_indexed_file.close()

    def _load_types(self, types_path):
        total_lines = line_counting.cached_counter.count_lines(types_path)
        self.logger.print_info('Reading types file: %s...' % types_path)
        with open(types_path, 'rb') as fin:
            reader = csv.reader(fin, delimiter=self.delimiter)
            for name, inst_type in tqdm(reader, total=total_lines):
                self.types.setdefault(name, []).append(inst_type)

    def _load_type_inheritance(self,  type_inheritance_path):
        total_lines = line_counting.cached_counter.count_lines(type_inheritance_path)
        self.logger.print_info('Reading type inheritance file...')
        with open(type_inheritance_path, 'rb') as fin:
            reader = csv.reader(fin, delimiter=self.delimiter)
            for inst_type, parent_type in tqdm(reader, total=total_lines):
                self.parent_types[inst_type] = parent_type

    def get_types(self, entity):
        types = []
        if entity in self.types:
            for entry in self.types[entity]:
                if self.is_number(entry):
                    self.types_indexed_file.seek(int(entry))
                    while True:
                        line = self.types_indexed_file.readline()
                        entity_name, entity_type = line.replace("\n", '').split(self.delimiter)
                        if not entity == entity_name:
                            break
                        types.append(entity_type)
                else:
                    types.append(entry)
        return types

    @staticmethod
    def is_number(s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    def count_types(self, name):
        counter = Counter(self.get_types(name))
        return counter

    def _get_parent_type(self, type_name):
        if type_name in self.parent_types:
            return self.parent_types[type_name]
        return None

    def get_transitive_types(self, types):
        new_types = Counter(types)
        for type, count in types.most_common():
            parent = self._get_parent_type(type)
            while parent is not None:
                new_types[parent] += count
                parent = self._get_parent_type(parent)
        assert sum(new_types.itervalues()) >= sum(types.itervalues())
        return new_types

if __name__ == '__main__':
    instance_types = EntityTypes()
    print(instance_types.get_types(".kw"))
    print(instance_types.get_types("Steve Jobs"))
    print(instance_types.get_types("Bremen"))
