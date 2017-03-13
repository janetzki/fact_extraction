import imp
from tqdm import tqdm
import unicodecsv

logger = imp.load_source('logger', '../logging/logger.py')
from logger import Logger

entity_types = imp.load_source('entity_types', '../ontology_building/entity_types.py')
from entity_types import EntityTypes

line_counting = imp.load_source('line_counting', '../helper_functions/line_counting.py')

class TypesIntegrator(object):
    def __init__(self):
        self.logger = Logger.from_config_file()
        self.delimiter = '#'
        self.join_character = '_'
        self.instance_types = EntityTypes(types_paths=['../data/types_en.csv'], types_indexed_file=False)

    def integrate_types_indices(self, types_path='../data/yago_types.csv',
                        output_path='../data/yago_index.csv'):
        total_lines = line_counting.cached_counter.count_lines(types_path)
        character_offset = 0
        entities = {}
        self.logger.print_info('Reading types file: %s...' % types_path)
        with open(types_path, 'rb') as fin:
            recent = ''
            for line in tqdm(iter(fin.readline, ''), total=total_lines):
                entity = line.split(self.delimiter)[0]
                if recent != entity:
                    recent = entity
                    if entity not in entities:
                        entities[entity] = self.join_character.join(self.instance_types.get_types(entity))

                    entities[entity] += self.join_character + str(character_offset)

                character_offset = fin.tell()

        self.logger.print_info('Writing index file %s' % output_path)
        with open(output_path, 'wb') as csv_file:
            writer = unicodecsv.writer(csv_file, delimiter=self.delimiter)
            for key, value in tqdm(entities.items(), total=len(entities)):
                writer.writerow([key, value])

if __name__ == '__main__':
    integrator = TypesIntegrator()
    integrator.integrate_types_indices()

