import imp
from collections import Counter

config_initializer = imp.load_source('config_initializer', '../config_initializer/config_initializer.py')
from config_initializer import ConfigInitializer

fact_extractor = imp.load_source('fact_extractor', '../pattern_recognition/fact_extractor.py')
from fact_extractor import FactExtractor

ttl_parser = imp.load_source('ttl_parser', '../ttl_parsing/ttl_parser.py')
from ttl_parser import TTLParser

logger = imp.load_source('logger', '../logging/logger.py')
from logger import Logger

test_data = imp.load_source('test_data', '../pattern_testing/test_data.py')


class PatternTester(ConfigInitializer):
    def __init__(self, facts_limit, randomize=False, ground_truth_path='../data/ground_truth.ttl'):
        self.facts_limit = facts_limit
        self.randomize = randomize
        self.ttl_parser = TTLParser(ground_truth_path, randomize)
        self.logger = Logger.from_config_file()
        self.results = {}
        self.fact_extractor = None

        # count known, right and wrong facts for each relationship
        self.known_facts_counter = Counter()
        self.right_facts_counter = Counter()
        self.wrong_facts_counter = Counter()

    @classmethod
    def from_config_file(cls):
        config_parser = cls.get_config_parser()
        facts_limit = config_parser.getint('pattern_testing', 'facts_limit')
        randomize = config_parser.getboolean('pattern_testing', 'randomize')
        return cls(facts_limit, randomize)

    def _collect_testing_facts(self):
        if self.fact_extractor is None:
            self.fact_extractor = FactExtractor.from_config_file()
            self.fact_extractor.set_print_interim_results(False)

        training_resources = self.fact_extractor.training_resources
        training_relations = self.fact_extractor.training_relationships
        entities = dict()
        fact_counter = 0

        self.logger.print_info('Collecting facts for testing...')
        for subject, predicate, object in self.ttl_parser.yield_entries():
            if fact_counter == self.facts_limit * len(training_relations):
                break
            if subject in training_resources:
                self.logger.print_error(
                    'Resource: "' + subject + '" was already used for training and thus won\'t be used for testing')
                continue
            if predicate not in training_relations:
                continue
            if self.known_facts_counter[predicate] == self.facts_limit:
                continue

            # maintain a dict for each entity with given relations as key
            # and their target values as list
            entities.setdefault(subject, []).append((predicate, object))
            self.known_facts_counter[predicate] += 1
            fact_counter += 1

        return entities

    def get_testing_resources(self):
        return set([subject for subject, predicate, object in self.ttl_parser.yield_entries()])

    def test_patterns(self):
        test_entities = self._collect_testing_facts()

        for test_entity in test_entities:
            extracted_facts = self.fact_extractor.extract_facts_from_resource(test_entity)
            for fact in extracted_facts:
                print(fact)
                subject, predicate, object, score, nl_sentence = fact
                assert subject == test_entity
                if (predicate, object) in test_entities[subject]:
                    self.right_facts_counter[predicate] += 1
                    print('Match')
                else:
                    self.wrong_facts_counter[predicate] += 1
                    print('No match')
                print('')

    @staticmethod
    def _calculate_f_measure(precision, recall):
        if precision is None or recall is None or precision + recall == 0:
            return None
        numerator = 2 * (precision * recall)
        return numerator / (precision + recall)

    @staticmethod
    def _soft_division(dividend, divisor):
        try:
            return dividend / float(divisor)
        except ZeroDivisionError:
            return None

    @staticmethod
    def _calculate_precision_recall_and_f_measure(total, right, wrong):
        precision = PatternTester._soft_division(right, right + wrong)
        recall = PatternTester._soft_division(right, total)
        f_measure = PatternTester._calculate_f_measure(precision, recall)
        return precision, recall, f_measure

    def print_results(self):
        for relationship in self.fact_extractor.training_relationships:
            total = self.known_facts_counter[relationship]
            right = self.right_facts_counter[relationship]
            wrong = self.wrong_facts_counter[relationship]
            precision, recall, f_measure = PatternTester._calculate_precision_recall_and_f_measure(total, right, wrong)
            print(relationship + ' Known facts:' + str(total) + ' Right:' + str(right) + ' Wrong:' + str(wrong)
                  + ' Precision:' + str(precision) + ' Recall:' + str(recall) + ' F-Measure:' + str(f_measure))


def compare_facts(extracted_facts, reference_facts, logger):
    extracted_facts = set([(resource, rel, obj) for (resource, rel, obj, score, nl_sentence) in extracted_facts])
    reference_facts = set(reference_facts)
    equal = extracted_facts == reference_facts
    if equal:
        logger.print_pass('Facts are equal.')
    else:
        logger.print_fail((str(extracted_facts) + ' does not equal: ' + str(reference_facts)))


def small_test():
    fact_extractor = FactExtractor.from_config_file()
    logger = Logger.from_config_file()
    for test_case in test_data.test_articles_list():
        html = test_case[0]
        resource = test_case[1]
        expected_facts = test_case[2]
        extracted_facts = fact_extractor.extract_facts_from_html(html, resource)
        compare_facts(extracted_facts, expected_facts, logger)


def large_test():
    pattern_tester = PatternTester.from_config_file()
    pattern_tester.test_patterns()
    pattern_tester.print_results()


if __name__ == '__main__':
    # small_test()
    large_test()
