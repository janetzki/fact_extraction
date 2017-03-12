from __future__ import print_function
import imp
import operator
import time
from collections import Counter
from tqdm import tqdm
import unicodecsv

ttl_parser = imp.load_source('ttl_parser', '../ttl_parsing/ttl_parser.py')
from ttl_parser import TTLParser

entity_types = imp.load_source('entity_types', '../ontology_building/entity_types.py')
from entity_types import EntityTypes

logger = imp.load_source('logger', '../logging/logger.py')
from logger import Logger

uri_rewriting = imp.load_source('uri_rewriting', '../helper_functions/uri_rewriting.py')
line_counting = imp.load_source('line_counting', '../helper_functions/line_counting.py')

class StatisticGenerator(object):

    def __init__(self, resources_path='../data/mappingbased_objects_en.ttl', facts_limit=100000):
        self.instance_types = EntityTypes(types_paths=["../data/types_en.csv"], types_index=False,
                 types_indexed_file=False)
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

    def test_types_independence(self, expectation_threshold = 10, ):
        variances = {}
        total_included_count = 0
        sum_avg_variance = 0

        self.logger.print_info('Collecting subject and object types for each predicate and calculating independence score...')
        for predicate in tqdm(self.predicates, total=len(self.predicates)):
            predicate_count = 0
            predicate_subject_types = Counter()
            predicate_object_types = Counter()
            combinations = Counter()
            for subject in self.predicates[predicate]:
                subject_types = self.instance_types.get_types(subject)
                for object in self.predicates[predicate][subject]:
                    # optional check for occurrence in Wikipedia article
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

    @staticmethod
    def calculate_independence_score(facts_count, subject_types, object_types, combinations, expectation_threshold):
        sum_rel_variance = 0

        # # kick out combinations with expected counts less than threshold
        # for combination, observed_count in combinations.most_common():
        #     subject, object = combination
        #     expected_count = float(subject_types[subject] * object_types[object]) / facts_count
        #     if expected_count >= threshold:
        #         filtered_combinations.update({combination: observed_count})
        #         expected_total += expected_count
        #     else:
        #         subject_types.subtract({subject: observed_count})
        #         object_types.subtract({object: observed_count})
        #
        # for combination, observed_count in filtered_combinations.most_common():
        #     subject, object = combination
        #     expected_count = float(subject_types[subject] * object_types[object]) / facts_count
        #     assert expected_count >= threshold
        #     expected_total += expected_count


        # avg_count = combination_count / float(unique_combination_count)
        # print "Average count per combination: ", avg_count

        # observed_total = sum(combinations.values())
        # print(combinations)
        # print(subject_types)
        # print(object_types)
        # combination_count = len(list(combinations))
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
    limits = [100000, 1000000, 5000000, 8000000]
    thresholds = [1, 2, 3, 5, 8, 10, 15]
    statistic_generator = StatisticGenerator()
    for l in limits:
        statistic_generator.collect_predicates(facts_limit=l)
        for t in thresholds:
            statistic_generator.test_types_independence(expectation_threshold=t)
