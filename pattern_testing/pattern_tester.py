import imp
from tqdm import tqdm
from collections import Counter

config_initializer = imp.load_source('config_initializer', '../config_initializer/config_initializer.py')
from config_initializer import ConfigInitializer

fact_extractor = imp.load_source('fact_extractor', '../pattern_recognition/fact_extractor.py')
from fact_extractor import FactExtractor

ttl_parser = imp.load_source('ttl_parser', '../ttl_parsing/ttl_parser.py')
from ttl_parser import TTLParser


class PatternTester(ConfigInitializer):
    def __init__(self, facts_limit, randomize=False, fact_extractor=None,
                 ground_truth_path='../data/ground_truth.ttl'):
        self.facts_limit = facts_limit
        self.randomize = randomize
        self.ttl_parser = TTLParser(ground_truth_path, randomize)
        self.results = {}

        # count known, right and wrong facts for each relationship
        self.known_facts_counter = Counter()
        self.right_facts_counter = Counter()
        self.wrong_facts_counter = Counter()

        if fact_extractor is not None:
            self.fact_extractor = fact_extractor
        else:
            self.fact_extractor = FactExtractor.from_config_file()
            self.fact_extractor.set_print_interim_results(False)

    @classmethod
    def from_config_file(cls):
        config_parser = cls.get_config_parser()
        facts_limit = config_parser.getint('pattern_testing', 'facts_limit')
        randomize = config_parser.getboolean('pattern_testing', 'randomize')
        return cls(facts_limit, randomize)

    def _collect_testing_facts(self):
        training_resources = self.fact_extractor.training_resources
        training_relations = self.fact_extractor.training_relationships

        entities = dict()
        fact_counter = 0

        tqdm.write('\n\nCollecting facts for testing...')
        for subject, predicate, object in self.ttl_parser.yield_entries():
            if fact_counter == self.facts_limit * len(training_relations):
                break
            # if subject in training_resources:  # TODO: issue #73
            #     continue
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


if __name__ == '__main__':
    pattern_tester = PatternTester.from_config_file()
    pattern_tester.test_patterns()
    pattern_tester.print_results()
