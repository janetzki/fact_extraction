import imp
import sys
from tqdm import tqdm
from collections import Counter

type_tool = imp.load_source('type_tool', '../storing_tools/type_tool.py')
from type_tool import TypeTool

type_pattern = imp.load_source('type_pattern', '../type_learning/type_pattern.py')
from type_pattern import TypePattern

ttl_parser = imp.load_source('ttl_parser', '../ttl_parsing/ttl_parser.py')
from ttl_parser import TTLParser

entity_types = imp.load_source('entity_types', '../ontology_building/entity_types.py')
from entity_types import EntityTypes

line_counting = imp.load_source('line_counting', '../helper_functions/line_counting.py')
uri_rewriting = imp.load_source('uri_rewriting', '../helper_functions/uri_rewriting.py')


class TypeLearner(TypeTool):
    def __init__(self, facts_path='../data/mappingbased_objects_en.ttl', output_path='../data/type_patterns_raw.pkl',
                 facts_limit=False):
        super(TypeLearner, self).__init__(None, output_path)
        self.facts_path = facts_path
        self.output_path = output_path
        self.facts_limit = facts_limit if facts_limit > 0 else sys.maxint
        self.ttl_parser = TTLParser(facts_path)
        self.instance_types = EntityTypes()
        self.subjects = dict()
        self.objects = dict()
        self.type_patterns = dict()

    @classmethod
    def from_config_file(cls):
        config_parser = cls.get_config_parser()
        section = 'type_learner'
        facts_limit = config_parser.getint(section, 'facts_limit')
        return cls(facts_limit=facts_limit)

    @staticmethod
    def _update_entity_counter(entities, entity, predicate):
        entity = uri_rewriting.strip_cleaned_name(entity)
        entities.setdefault(entity, Counter())
        entities[entity][predicate] += 1

    def _count_predicates(self):
        total_lines = min(line_counting.cached_counter.count_lines(self.facts_path), self.facts_limit)
        facts_count = 0

        self.logger.print_info('Counting relations for subjects and objects...')
        for subject, predicate, object in tqdm(self.ttl_parser.yield_entries(), total=total_lines):
            facts_count += 1
            if facts_count > self.facts_limit:
                break

            self._update_entity_counter(self.subjects, subject, predicate)
            self._update_entity_counter(self.objects, object, predicate)

            self.type_patterns.setdefault(predicate, TypePattern())
            self.type_patterns[predicate].facts += 1

    def _get_types(self, entities):
        relations = dict()
        for entity in tqdm(entities, total=len(entities)):
            types = self.instance_types.get_types(entity)
            for predicate, quantity in entities[entity].iteritems():
                relations.setdefault(predicate, Counter())
                for type in types:
                    relations[predicate].update({type: quantity})
        return relations

    def _count_types(self):
        self.logger.print_info('Retrieving types for subjects...')
        subject_types = self._get_types(self.subjects)
        self.logger.print_info('Cumulating subject types for relations...')
        for predicate in tqdm(subject_types, total=len(subject_types)):
            self.type_patterns[predicate].subject_types += subject_types[predicate]

        self.logger.print_info('Retrieving types for objects...')
        object_types = self._get_types(self.objects)
        self.logger.print_info('Cumulating object types for relations...')
        for predicate in tqdm(object_types, total=len(object_types)):
            self.type_patterns[predicate].object_types += object_types[predicate]

    def learn_types(self):
        self.logger.print_info('Type learning...')
        self._count_predicates()
        self._count_types()
        self.logger.print_done('Type learning completed.')


if __name__ == '__main__':
    type_learner = TypeLearner.from_config_file()
    type_learner.learn_types()
    type_learner.save_type_patterns()
