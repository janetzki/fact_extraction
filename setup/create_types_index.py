from tqdm import tqdm
import os
import unicodecsv
from logger import Logger
from ontology_building import EntityTypes
from helper_functions import line_counting

dir_path = os.path.dirname(os.path.abspath(__file__)) + '/'


class TypesIntegrator(object):
    def __init__(self):
        self.logger = Logger.from_config_file()
        self.delimiter = '#'
        self.join_character = '_'
        self.instance_types = EntityTypes(types_paths=[dir_path + '../data/types_en.csv'], types_indexed_file=False)

    def integrate_types_indices(self, types_path=dir_path + '../data/yago_types.csv',
                                output_path=dir_path + '../data/yago_index.csv'):
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
