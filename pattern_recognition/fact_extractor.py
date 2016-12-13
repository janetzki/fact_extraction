import pickle
import sys
import csv
import imp
from tqdm import tqdm
from bs4 import BeautifulSoup as bs
from random import randint

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

            if True:  # self.randomize:
                random_offset = 1000  # randint(0, 10000)
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

    def discover_facts_in_sentences(self, sentences):
        facts = []
        for sent in tqdm(sentences, total=len(sentences)):
            relative_position = sent.calculate_relative_position()
            soup = bs(sent.as_string(), 'lxml')
            nl_sentence = soup.get_text()
            object_tokens_of_references = self.wikipedia_connector.find_tokens_of_references_in_html(sent.as_string())
            for object_resource, object_tokens in object_tokens_of_references:
                pattern = pattern_extractor.extract_pattern(nl_sentence, object_tokens, relative_position)
                if pattern is None:
                    continue
                matching_relations = self.match_pattern_against_relation_patterns(pattern)
                new_facts = [(rel, object_resource, score, nl_sentence) for (rel, score) in matching_relations]
                facts.extend(new_facts)
                for fact in new_facts:
                    print
                    print fact
        return facts

    def extract_facts(self):
        facts = []
        print('Fact extraction...')
        for resource in self.discovery_resources:
            print('--- ' + resource + ' ----')
            html_text = self.wikipedia_connector.get_wikipedia_article(resource)
            sentences = self.wikipedia_connector.html_sent_tokenize(html_text)
            tagged_sentences = self.wikipedia_connector.make_to_tagged_sentences(sentences)
            referenced_sentences = filter(
                lambda sent: self.wikipedia_connector.contains_any_reference(sent.as_string()), tagged_sentences)
            new_facts = self.discover_facts_in_sentences(referenced_sentences)
            new_facts = [(resource, rel, obj, score, nl_sentence) for (rel, obj, score, nl_sentence) in new_facts]
            facts.extend(new_facts)

        facts.sort(key=lambda fact: fact[3], reverse=True)
        print('\n----- Extracted facts ------')
        for fact in facts:
            print fact


def parse_input_parameters():
    use_dump, randomize = False, False
    helped = False

    for arg in sys.argv[1:]:
        if arg == '--dump':
            use_dump = True
        elif arg == '--rand':
            randomize = True
        elif not helped:
            print 'Usage: python fact_extractor.py [--dump] [--rand]'
            helped = True

    return use_dump, randomize


if __name__ == '__main__':
    use_dump, randomize = parse_input_parameters()
    fact_extractor = FactExtractor(1, use_dump=use_dump, randomize=randomize)
    fact_extractor.extract_facts()
