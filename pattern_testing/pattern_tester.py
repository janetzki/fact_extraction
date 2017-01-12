import imp
from tqdm import tqdm
from collections import Counter

config_initializer = imp.load_source('config_initializer', '../config_initializer/config_initializer.py')
from config_initializer import ConfigInitializer

fact_extractor = imp.load_source('fact_extractor', '../pattern_recognition/fact_extractor.py')
from fact_extractor import FactExtractor

dbpedia_dump_extractor = imp.load_source('dbpedia_dump_extractor', '../dbpedia_connector/dbpedia_dump_extractor.py')
from dbpedia_dump_extractor import DBpediaDumpExtractor


class PatternTester(ConfigInitializer):
    def __init__(self, facts_limit, randomize=False, fact_extractor=None,
                 resources_path='../data/mappingbased_objects_en.ttl'):
        self.facts_limit = facts_limit
        self.randomize = randomize
        self.dbpedia_dump_extractor = DBpediaDumpExtractor(resources_path, randomize)
        self.results = {}

        # count right and wrong facts for each relation
        self.right_facts_counter = Counter()
        self.wrong_facts_counter = Counter()

        if fact_extractor is not None:
            self.fact_extractor = fact_extractor
        else:
            self.fact_extractor = FactExtractor.from_config_file()
            self.fact_extractor.set_print_interim_results(False)

    @classmethod
    def from_config_file(cls, path='../config.ini'):
        config_parser = cls.get_config_parser(path)
        facts_limit = config_parser.getint('pattern_testing', 'facts_limit')
        randomize = config_parser.getboolean('pattern_testing', 'randomize')
        return cls(facts_limit, randomize)

    def _collect_testing_facts(self):
        training_resources = self.fact_extractor.training_resources
        training_relations = self.fact_extractor.training_relations

        entities = dict()
        relation_types_counter = Counter()
        fact_counter = 0

        tqdm.write('\n\nCollecting facts for testing...')
        for subject, predicate, object in self.dbpedia_dump_extractor.yield_entries():
            if fact_counter == self.facts_limit * len(training_relations):
                break
            if subject in training_resources:
                continue
            if predicate not in training_relations:
                continue
            if relation_types_counter[predicate] == self.facts_limit:
                continue

            # maintain a dict for each entity with given relations as key
            # and their target values as list
            entities.setdefault(subject, []).append((predicate, object))
            relation_types_counter[predicate] += 1
            fact_counter += 1

        return entities

    def test_patterns(self):
        test_entities = self._collect_testing_facts()

        for test_entity in test_entities:
            extracted_facts = self.fact_extractor.extract_facts_from_resource(test_entity)
            for fact in extracted_facts:
                subject, predicate, object, score, nl_sentence = fact
                assert subject == test_entity
                if (predicate, object) in test_entities[subject]:
                    self.right_facts_counter[predicate] += 1
                else:
                    self.wrong_facts_counter[predicate] += 1

    @staticmethod
    def calculate_f_measure(precision, recall):
        return 2 * (precision * recall) / (precision + recall)

    def print_results(self):
        for relation in self.fact_extractor.training_relations:
            total = self.facts_limit
            right = self.right_facts_counter[relation]
            wrong = self.wrong_facts_counter[relation]
            precision = right / (right + wrong)
            recall = right / total
            f_measure = PatternTester.calculate_f_measure(precision, recall)
            print(relation + ' ' + total + ' ' + right + ' ' + wrong + ' ' + precision + ' ' + recall + ' ' + f_measure)


if __name__ == '__main__':
    pattern_tester = PatternTester.from_config_file()
    pattern_tester.test_patterns()
    pattern_tester.print_results()
