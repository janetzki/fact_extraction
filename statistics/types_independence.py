from __future__ import print_function
import imp
import operator
import time
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
from tqdm import tqdm
import unicodecsv

ttl_parser = imp.load_source('ttl_parser', '../ttl_parsing/ttl_parser.py')
from ttl_parser import TTLParser

entity_types = imp.load_source('entity_types', '../ontology_building/entity_types.py')
from entity_types import EntityTypes

pattern = imp.load_source('pattern', '../pattern_learning/pattern.py')
from pattern import Pattern

logger = imp.load_source('logger', '../logging/logger.py')
from logger import Logger

uri_rewriting = imp.load_source('uri_rewriting', '../helper_functions/uri_rewriting.py')
line_counting = imp.load_source('line_counting', '../helper_functions/line_counting.py')


class StatisticGenerator(object):

    def __init__(self, resources_path='../data/mappingbased_objects_en.ttl', facts_limit=100000):
        # self.instance_types = EntityTypes(types_paths=["../data/types_en.csv"], types_index=False,
        #          types_indexed_file=False)
        self.instance_types = EntityTypes()
        self.resources_path = resources_path
        self.ttl_parser = TTLParser(resources_path, False)
        self.logger = Logger.from_config_file()
        self.delimiter = '#'
        self.predicates = dict()
        self.facts_limit = facts_limit

    def collect_predicates(self, facts_limit=100000):
        self.facts_limit = facts_limit
        self.predicates = dict()
        total_count = 0
        total_lines = min(line_counting.cached_counter.count_lines(self.resources_path), self.facts_limit)

        self.logger.print_info('Collecting facts for each predicate...')
        for subject, predicate, object in tqdm(self.ttl_parser.yield_entries(), total=total_lines):
            total_count += 1
            if total_count > self.facts_limit:
                break

            subject = uri_rewriting.strip_cleaned_name(subject)
            object = uri_rewriting.strip_cleaned_name(object)

            self.predicates.setdefault(predicate, {}).setdefault(subject, []).append(object)

    def count_types(self):
        subject_counts = []
        object_counts = []
        has_both = 0
        has_exact_one = 0
        has_nothing = 0
        facts = 0
        outlier_threshold = 100

        for predicate in tqdm(self.predicates, total=len(self.predicates)):
            for subject in self.predicates[predicate]:
                subject_types = self.instance_types.get_types(subject)

                for object in self.predicates[predicate][subject]:
                    object_types = self.instance_types.get_types(object)

                    facts += 1
                    if subject_types:
                        if len(subject_types) < outlier_threshold:
                            subject_counts.append(len(subject_types))
                    if object_types:
                        if len(object_types) < outlier_threshold:
                            object_counts.append(len(object_types))
                    if subject_types and object_types:
                        has_both += 1
                    if not subject_types and not object_types:
                        has_nothing += 1
                    if (len(subject_types) > 0) ^ (len(object_types) > 0):
                        has_exact_one += 1

        subject_counts = pd.Series(subject_counts)
        #subject_counts.plot.hist(bins=100)
        #plt.show()
        object_counts = pd.Series(object_counts)
        #object_counts.plot.hist(bins=100)
        #plt.show()
        self.logger.print_info('Facts: ' + str(facts))
        self.logger.print_info('With subject type: ' + str(subject_counts.count()))
        self.logger.print_info('Mean subject type count: ' + str(subject_counts.mean()))
        self.logger.print_info('Standard deviation subject type count: ' + str(subject_counts.std()))
        self.logger.print_info('With object type: ' + str(object_counts.count()))
        self.logger.print_info('Mean object type count: ' + str(object_counts.mean()))
        self.logger.print_info('Standard deviation object type count: ' + str(object_counts.std()))
        self.logger.print_info('Both with type(s): ' + str(has_both))
        self.logger.print_info('Exact one with type(s): ' + str(has_exact_one))
        self.logger.print_info('None with type(s): ' + str(has_nothing))

    def test_types_independence(self, expectation_threshold = 10):
        variances = {}
        total_included_count = 0
        sum_avg_variance = 0
        empty_token = '#empty'

        self.logger.print_info('Collecting subject and object types for each predicate and calculating independence score...')
        for predicate in tqdm(self.predicates, total=len(self.predicates)):
            predicate_count = 0
            predicate_subject_types = Counter()
            predicate_object_types = Counter()
            combinations = Counter()
            for subject in self.predicates[predicate]:
                subject_types = self.instance_types.get_types(subject).append(empty_token)
                for object in self.predicates[predicate][subject]:
                    # TODO: check for occurrence in Wikipedia article
                    # TODO: exclude double underscores
                    predicate_count += 1
                    object_types = self.instance_types.get_types(object)
                    predicate_subject_types.update(subject_types)
                    predicate_object_types.update(object_types)
                    cross_product = [(s, o) for s in subject_types for o in object_types]
                    combinations.update(cross_product)

            # print(predicate)
            variance = StatisticGenerator.calculate_independence_score(predicate_count, predicate_subject_types,
                                                         predicate_object_types, combinations,
                                                         expectation_threshold)
            if variance is None:
                continue

            variances[predicate] = variance
            sum_avg_variance += float(predicate_count) * variance
            total_included_count += predicate_count

        total_avg_variance = sum_avg_variance / total_included_count

        with open("types_independence_" + str(int(time.time())) + ".csv", 'wb') as csv_file:
            writer = unicodecsv.writer(csv_file, delimiter=self.delimiter)
            writer.writerow(["Threshold", expectation_threshold,
                             "Facts count", self.facts_limit,
                             "Avg variance", total_avg_variance])
            for predicate, variance in sorted(variances.items(), key=operator.itemgetter(1)):
                writer.writerow([predicate, variance])
                print(predicate, " ", variance)

    def measure_type_diversity(self, threshold=2):
        subject_types_count = Counter()
        object_types_count = Counter()
        relation_subject_types = {}
        relation_object_types = {}

        facts = Counter()

        for predicate in tqdm(self.predicates, total=len(self.predicates)):
            relation_subject_types[predicate] = Counter()
            relation_object_types[predicate] = Counter()
            for subject in self.predicates[predicate]:
                subject_types = self.instance_types.get_types(subject)

                for object in self.predicates[predicate][subject]:
                    object_types = self.instance_types.get_types(object)

                    facts[predicate] += 1
                    for subject_type in subject_types:
                        relation_subject_types[predicate][subject_type] += 1
                        subject_types_count[subject_type] += 1
                    for object_type in object_types:
                        relation_object_types[predicate][object_type] += 1
                        object_types_count[object_type] += 1
                    #print(predicate, subject, object)

        subject_specs = StatisticGenerator.calculate_specifity(facts, subject_types_count, relation_subject_types)
        object_specs = StatisticGenerator.calculate_specifity(facts, object_types_count, relation_object_types)
        both_specs = {}
        for predicate in subject_specs:
            both_specs[predicate] = {}
            both_specs[predicate]["subject"] = subject_specs[predicate]
        for predicate in object_specs:
            both_specs.setdefault(predicate, {})
            both_specs[predicate]["object"] = object_specs[predicate]
        for predicate in both_specs:
            print(';'.join([predicate, str(both_specs[predicate].setdefault("subject", -1)), str(both_specs[predicate].setdefault("object", -1))]))

    @staticmethod
    def calculate_specifity(facts, types, relation_types):
        total_facts = sum(facts.values())
        specifities = {}

        for predicate in relation_types:
            if len(set(relation_types[predicate])) == 0:
                continue

            deviations = 0
            for name, predicate_type_frequency in relation_types[predicate].most_common():
                predicate_relative_frequency = float(predicate_type_frequency) / facts[predicate]
                total_frequency = float(types[name]-predicate_type_frequency) / total_facts
                # print(name)
                # print(facts[predicate])
                # print(predicate_frequency)
                # print(predicate_relative_frequency)
                # print(total_frequency)
                assert abs(predicate_relative_frequency-total_frequency) <= 1
                deviations += predicate_type_frequency * abs(predicate_relative_frequency-total_frequency)
            specifities[predicate] = float(deviations) / sum(relation_types[predicate].values())
        return specifities

    @staticmethod
    def calculate_independence_score(facts_count, subject_types, object_types, combinations, expectation_threshold):
        sum_rel_variance = 0
        included_combination_count = 0

        for combination, observed_count in combinations.most_common():
            subject, object = combination
            expected_count = float(subject_types[subject] * object_types[object]) / facts_count
            if expected_count < expectation_threshold:
                continue
            included_combination_count += observed_count
            rel_variance = (float(abs(observed_count-expected_count)) / expected_count)
            sum_rel_variance += observed_count * rel_variance

        if included_combination_count == 0:
            return None
        return sum_rel_variance / included_combination_count

if __name__ == '__main__':
    statistic_generator = StatisticGenerator()

    # limits = [100000, 1000000, 5000000, 8000000]
    # thresholds = [1, 2, 3, 5, 8, 10, 15]
    # for l in limits:
    #     statistic_generator.collect_predicates(facts_limit=l)
    #     for t in thresholds:
    #         statistic_generator.test_types_independence(expectation_threshold=t)

    statistic_generator.collect_predicates(facts_limit=1000000)
    statistic_generator.measure_type_diversity()
    #statistic_generator.count_types()
