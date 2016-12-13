import pickle
import sys
import csv
import imp
from tqdm import tqdm
from bs4 import BeautifulSoup as bs
from random import randint
from ConfigParser import SafeConfigParser

pattern_extractor = imp.load_source('pattern_extractor', '../pattern_learning/pattern_extractor.py')
wikipedia_connector = imp.load_source('wikipedia_connector', '../wikipedia_connector/wikipedia_connector.py')
from pattern_extractor import Pattern
from wikipedia_connector import WikipediaConnector


class FactExtractor(object):
    def __init__(self, limit, use_dump=False, randomize=False, match_threshold=0.05, load_path='../data/patterns.pkl',
                 resources_path='../data/mappingbased_objects_en_filtered.csv'):
        self.limit = limit
        self.use_dump = use_dump
        self.randomize = randomize
        self.match_threshold = match_threshold
        self.load_path = load_path
        self.resources_path = resources_path
        self.training_resources = set()
        self.discovery_resources = set()
        self.relation_patterns = {}
        self.wikipedia_connector = WikipediaConnector(self.use_dump)

        self.load_patterns()
        self.load_discovery_resources()

    def load_patterns(self):
        with open(self.load_path, 'rb') as fin:
            self.training_resources, self.relation_patterns = pickle.load(fin)

    def load_discovery_resources(self):
        with open(self.resources_path, 'r') as f:
            wikireader = csv.reader(f, delimiter=' ', quotechar='"')

            if self.randomize:
                random_offset = randint(0, 10000)
                for row in wikireader:
                    random_offset -= 1
                    if random_offset == 0:
                        break

            max_results = self.limit
            for row in wikireader:
                if max_results == 0:
                    break
                subject = row[0]
                if subject not in self.training_resources and subject not in self.discovery_resources:
                    self.discovery_resources.add(subject)
                    max_results -= 1

    def match_pattern_against_relation_patterns(self, pattern):
        matching_relations = []
        for relation, relation_pattern in self.relation_patterns.iteritems():
            match_score = Pattern.match_patterns_bidirectional(relation_pattern, pattern)
            if match_score >= self.match_threshold:
                matching_relations.append((relation, match_score))
        return matching_relations

    def extract_facts_from_sentences(self, sentences):
        facts = []
        for sent in tqdm(sentences, total=len(sentences)):
            relative_position = sent.relative_pos
            nl_sentence = sent.as_string()
            object_addresses_of_links = sent.addresses_of_links()
            for object_link, object_addresses in object_addresses_of_links.iteritems():
                pattern = pattern_extractor.extract_pattern(nl_sentence, object_addresses, relative_position)
                if pattern is None:
                    continue
                matching_relations = self.match_pattern_against_relation_patterns(pattern)
                new_facts = [(rel, object_link, score, nl_sentence) for (rel, score) in matching_relations]
                facts.extend(new_facts)
                for fact in new_facts:
                    print('')
                    print(fact)
        return facts

    def extract_facts(self):
        facts = []
        print('Fact extraction...')
        for resource in self.discovery_resources:
            print('--- ' + resource + ' ----')
            tagged_sentences = self.wikipedia_connector.get_parsed_wikipedia_article(resource)
            referenced_sentences = filter(lambda sent: sent.contains_any_link(), tagged_sentences)
            new_facts = self.extract_facts_from_sentences(referenced_sentences)
            new_facts = [(resource, rel, obj, score, nl_sentence) for (rel, obj, score, nl_sentence) in new_facts]
            facts.extend(new_facts)

        facts.sort(key=lambda fact: fact[3], reverse=True)
        print('\n----- Extracted facts ------')
        for fact in facts:
            print fact


def get_input_parameters_from_file(path):
    config = SafeConfigParser()
    config.read(path)
    use_dump = config.getboolean('general', 'use_dump')
    randomize = config.getboolean('fact_extractor', 'randomize')
    limit = config.getint('fact_extractor', 'limit')
    return use_dump, randomize, limit


if __name__ == '__main__':
    use_dump, randomize, limit = get_input_parameters_from_file('../config.ini')
    fact_extractor = FactExtractor(limit, use_dump=use_dump, randomize=randomize)
    fact_extractor.extract_facts()
