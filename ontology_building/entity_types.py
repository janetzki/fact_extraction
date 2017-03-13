from tqdm import tqdm
from collections import Counter
import csv
import imp

logger = imp.load_source('logger', '../logging/logger.py')
from logger import Logger

line_counting = imp.load_source('line_counting', '../helper_functions/line_counting.py')


class EntityTypes(object):
    def __init__(self, types_path='../data/types_en.csv',
                 type_inheritance_path='../data/types_inheritance_en.csv'):
        self.logger = Logger.from_config_file()
        self.types = {}
        self.parent_types = {}
        self.delimiter = '#'
        self._load_types(types_path, type_inheritance_path)

    def _load_types(self, types_path, type_inheritance_path):
        total_lines = line_counting.cached_counter.count_lines(types_path)
        self.logger.print_info('Reading types file...')
        with open(types_path, 'rb') as fin:
            reader = csv.reader(fin, delimiter=self.delimiter)
            for name, inst_type in tqdm(reader, total=total_lines):
                self.types.setdefault(name, []).append(inst_type)

        total_lines = line_counting.cached_counter.count_lines(type_inheritance_path)
        self.logger.print_info('Reading type inheritance file...')
        with open(type_inheritance_path, 'rb') as fin:
            reader = csv.reader(fin, delimiter=self.delimiter)
            for inst_type, parent_type in tqdm(reader, total=total_lines):
                self.parent_types[inst_type] = parent_type

    def count_types(self, name):
        counter = Counter()
        if name in self.types:
            counter = Counter(self.types[name])
        return counter

    def _get_parent_type(self, type_name):
        if type_name in self.parent_types:
            return self.parent_types[type_name]
        return False

    def get_transitive_types(self, types):
        new_types = Counter()
        for type in list(types):
            new_types[type] += 1
            parent = self._get_parent_type(type)
            while parent:
                new_types[parent] += 1
                parent = self._get_parent_type(parent)
        return new_types
