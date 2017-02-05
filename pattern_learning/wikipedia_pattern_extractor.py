from __future__ import division
from termcolor import colored
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag_sents
from ascii_graph import Pyasciigraph
from collections import Counter
from tqdm import tqdm
from pattern_extractor import PatternExtractor, Pattern
import re
import imp
import pickle
import itertools

config_initializer = imp.load_source('config_initializer', '../config_initializer/config_initializer.py')
from config_initializer import ConfigInitializer

wikipedia_connector = imp.load_source('wikipedia_connector', '../wikipedia_connector/wikipedia_connector.py')
from wikipedia_connector import WikipediaConnector

ttl_parser = imp.load_source('ttl_parser', '../ttl_parsing/ttl_parser.py')
from ttl_parser import TTLParser

uri_rewriting = imp.load_source('uri_rewriting', '../helper_functions/uri_rewriting.py')


class WikipediaPatternExtractor(ConfigInitializer):
    def __init__(self, relation_types_limit, facts_limit, resources_path='../data/mappingbased_objects_en.ttl',
                 relationships=None, use_dump=False, randomize=False, perform_tests=False, type_learning=True,
                 write_path='../data/patterns.pkl', replace_redirects=False,
                 least_threshold_types=1, least_threshold_words=2):
        self.use_dump = use_dump
        self.facts_limit = facts_limit
        self.perform_tests = perform_tests
        self.type_learning = type_learning
        self.least_threshold_types = least_threshold_types
        self.least_threshold_words = least_threshold_words
        self.write_path = write_path
        self.wikipedia_connector = WikipediaConnector(use_dump=self.use_dump, redirect=replace_redirects)
        self.pattern_extractor = PatternExtractor()
        self.ttl_parser = TTLParser(resources_path, randomize)

        if relationships is not None:
            self.relationships = ['http://dbpedia.org/ontology/' + r for r in relationships if r]
            self.relation_types_limit = len(self.relationships)
        else:
            self.relationships = None  # means any relation may be learned
            self.relation_types_limit = relation_types_limit

        self.dbpedia = {}
        self.relation_patterns = {}
        self.matches = []

    @classmethod
    def from_config_file(cls):
        config_parser = cls.get_config_parser()
        use_dump = config_parser.getboolean('general', 'use_dump')

        randomize = config_parser.getboolean('wiki_pattern', 'randomize')
        perform_tests = config_parser.getboolean('wiki_pattern', 'randomize')
        relation_types_limit = config_parser.getint('wiki_pattern', 'relation_types_limit')
        facts_limit = config_parser.getint('wiki_pattern', 'facts_limit')
        replace_redirects = config_parser.getboolean('wiki_pattern', 'replace_redirects')
        type_learning = config_parser.getboolean('wiki_pattern', 'type_learning')
        least_threshold_types = config_parser.getfloat('wiki_pattern', 'least_threshold_types')
        least_threshold_words = config_parser.getfloat('wiki_pattern', 'least_threshold_words')
        relationships = config_parser.get('wiki_pattern', 'relationships')
        relationships = WikipediaPatternExtractor.split_string_list(relationships)
        return cls(relation_types_limit, facts_limit, relationships=relationships, use_dump=use_dump,
                   randomize=randomize,
                   perform_tests=perform_tests, replace_redirects=replace_redirects, type_learning=type_learning,
                   least_threshold_types=least_threshold_types, least_threshold_words=least_threshold_words)

    @staticmethod
    def split_string_list(string):
        return string.split(',')

    # -------------------------------------------------------------------------------------------------
    #                               Data Preprocessing
    # -------------------------------------------------------------------------------------------------

    def parse_dbpedia_data(self):
        """
        Takes all DBpedia ontology relations (subj verb target) stored in file_name
        and returns a dictionary with subjects as keys and all of their related information
        as dict values.
        more precisely {subj: { verb1: [val1, val2, val3...],
                                verb2: [val1, ...]
                            }
                        }
        """
        entities = dict()
        relation_types_counter = Counter()
        fact_counter = 0

        tqdm.write('\n\nCollecting facts for training...')
        for subject, predicate, object in self.ttl_parser.yield_entries():
            if fact_counter == self.facts_limit * self.relation_types_limit:
                break
            if len(relation_types_counter) == self.relation_types_limit and predicate not in relation_types_counter:
                continue
            if relation_types_counter[predicate] == self.facts_limit:
                continue
            if self.relationships is not None and predicate not in self.relationships:
                continue

            # maintain a dict for each entity with given relations as key
            # and their target values as list
            entities.setdefault(subject, {}).setdefault(predicate, []).append(object)
            relation_types_counter[predicate] += 1
            fact_counter += 1

        tqdm.write('\n\nRelation types:')
        most_common_relation_types = relation_types_counter.most_common()
        for i in range(len(most_common_relation_types)):
            relation_type, frequency = most_common_relation_types[i]
            print('\t' + str(i + 1) + ':\t' + str(frequency) + ' x\t' + relation_type).expandtabs(10)

        return entities

    def discover_patterns(self):
        """
        Preprocesses data (initializing main data structure)
        1. Filter relevant DBpedia facts by relationships -> still TODO
        2. Turn DBpedia data into in-memory dictionary where all processing takes place
        3. Fetch relevant Wikipedia articles and filter relevant sentences out of html text (for link search)
        4. Data is stored in self.dbpedia
        """
        # parse dbpedia information
        self.dbpedia = self.parse_dbpedia_data()

        tqdm.write('\n\nSentence extraction...')
        for entity, values in tqdm(self.dbpedia.iteritems(), total=len(self.dbpedia)):
            # for each relationship filter sentences that contain
            # target resources of entity's relationship
            for rel, resources in values.iteritems():
                wikipedia_target_resources = map(uri_rewriting.convert_to_internal_wikipedia_uri, resources)
                # retrieve tokenized wikipedia sentences that include DBpedia resources that we are looking for
                tagged_sentences = self.wikipedia_connector.get_filtered_wikipedia_article(entity,
                                                                                           wikipedia_target_resources)
                values[rel] = {'resources': wikipedia_target_resources,
                               'sentences': tagged_sentences,
                               'patterns': []}

    # ---------------------------------------------------------------------------------------------
    #                               Statistics and Visualizations
    # ---------------------------------------------------------------------------------------------

    def extract_patterns(self):
        color_mapping = {
            'magenta': ['NN', 'NNS'],
            'green': ['NNP', 'NNPS'],
            'cyan': ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ'],
            'yellow': ['JJ', 'JJR', 'JJS']
        }
        # reverse color mapping
        color_mapping = {v: k for k, values in color_mapping.iteritems() for v in values}

        tqdm.write('\n\nPattern extraction...')
        for entity, relations in tqdm(self.dbpedia.iteritems(), total=len(self.dbpedia)):
            cleaned_subject_entity_name = uri_rewriting.strip_cleaned_name(entity)
            subject_entity = uri_rewriting.strip_name(entity)
            for rel_ontology, values in relations.iteritems():
                target_resources = values['resources']
                sentences = values['sentences']
                rel_ontology = rel_ontology.split('/')[-1]
                data = [
                    {'entity': cleaned_subject_entity_name, 'relation': rel_ontology, 'resource': res, 'sentence': sent}
                    for res in target_resources
                    for sent in sentences
                    if sent.contains_any_link([res]) and res != entity]

                # remove needless sentence information based on relation facts
                # data = map(self.shorten_sentence, data)
                # POS tag sentences
                for entry in data:
                    sentence = entry['sentence']
                    if sentence.number_of_tokens() > 50:
                        continue  # probably too long for stanford tokenizer
                    resource = entry['resource']
                    nl_sentence = sentence.as_string()
                    relative_position = sentence.relative_pos
                    entry['nl sentence'] = nl_sentence
                    tokenized_sentences = map(word_tokenize, [nl_sentence])
                    pos_tagged_sentences = pos_tag_sents(tokenized_sentences).pop()

                    object_addresses = sentence.addresses_of_link(resource)
                    object_entity = uri_rewriting.strip_name(resource)
                    pattern = self.pattern_extractor.extract_pattern(nl_sentence, object_addresses, relative_position,
                                                                     self.type_learning, subject_entity, object_entity)

                    if pattern is not None:
                        values['patterns'].append(pattern)
                        entry['pattern'] = pattern

                    # color sentence parts according to POS tag
                    colored_sentence = [colored(word, color_mapping.setdefault(pos, 'white'))
                                        for word, pos in pos_tagged_sentences]
                    colored_sentence = ' '.join(colored_sentence)
                    colored_sentence = re.sub(r' (.\[\d+m),', ',', colored_sentence)  # remove space before commas
                    entry['colored_sentence'] = colored_sentence

                self.matches.extend(data)

        # drop duplicates
        self.matches.sort()
        self.matches = list(x for x, _ in itertools.groupby(self.matches))

    def print_occurences(self):
        """
        Prints each occurence of a given DBpedia fact with their corresponding and matched sentence.
        The matched sentence is POS tagges using maxent treebank pos tagging model.
        Nouns, verbs and adjectives are printed in colour.
        """

        for entry in self.matches:
            if not entry.get('colored_sentence', None):
                continue
            print(colored('[DBP Entitity] \t', 'red',
                          attrs={'concealed', 'bold'}) + colored(entry['entity'], 'white')).expandtabs(20)
            print(colored('[DBP Ontology] \t', 'red',
                          attrs={'concealed', 'bold'}) + colored(entry['relation'], 'white')).expandtabs(20)
            print(colored('[DBP Resource] \t', 'red',
                          attrs={'concealed', 'bold'}) + colored(uri_rewriting.strip_cleaned_name(entry['resource']),
                                                                 'white')).expandtabs(20)
            print(colored('[Wiki Occurence] \t',
                          'red', attrs={'concealed', 'bold'}) + entry['colored_sentence']).expandtabs(20)
            print('')

        print('[POS KEY]\t'
              + colored('NORMAL NOUN\t', 'magenta')
              + colored('PROPER NOUN\t', 'green')
              + colored('VERB\t', 'cyan')
              + colored('ADJ\t', 'yellow')).expandtabs(20)

    def count_matches(self):
        matches_count = {}
        for relation, pattern in self.relation_patterns.iteritems():
            matches_count[relation] = pattern.covered_sentences
        return matches_count

    def calculate_text_coverage(self):
        """ Prints CLI stats about percentage of matched dbpedia facts in wiki raw text.  """
        matched_count = self.count_matches()
        total_count = {}
        for entity, relationships in self.dbpedia.iteritems():
            for relation, values in relationships.iteritems():
                target_resources = values.get('resources', [])
                total_count.setdefault(relation, 0)
                total_count[relation] += len(target_resources)

        occurrence_count = {}
        for relation in total_count:
            occurrence_count[relation] = {'total': total_count[relation],
                                          'matched': matched_count.setdefault(relation, 0)}

        # print bar chart
        data = [('%  ' + str(vals['matched']) + '/' + str(vals['total']) + ' ' + rel.split('/')[-1],
                 vals['matched'] / vals['total'] * 100)
                for rel, vals in occurrence_count.iteritems()]
        graph = Pyasciigraph()
        for line in graph.graph('occured facts in percentage', data):
            print(line)

    def merge_patterns(self):
        tqdm.write('\n\nPattern merging...')
        for entity, relations in tqdm(self.dbpedia.iteritems()):
            for rel, values in relations.iteritems():
                for pattern in values['patterns']:
                    if rel in self.relation_patterns:
                        self.relation_patterns[rel] = Pattern.merge(self.relation_patterns[rel], pattern,
                                                                    self.perform_tests)
                    else:
                        self.relation_patterns[rel] = pattern

    def clean_patterns(self):
        tqdm.write('\n\nPattern cleaning...')
        for relation, pattern in tqdm(self.relation_patterns.iteritems()):
            self.relation_patterns[relation] = Pattern.clean_pattern(pattern,
                                                                     self.least_threshold_words,
                                                                     self.least_threshold_types)
        self.relation_patterns = dict(filter(lambda (rel, pat): pat is not None, self.relation_patterns.iteritems()))

    def save_patterns(self):
        print('\n\nPattern saving...')
        with open(self.write_path, 'wb') as fout:
            output = self.dbpedia.keys(), self.relation_patterns
            pickle.dump(output, fout, pickle.HIGHEST_PROTOCOL)


if __name__ == '__main__':
    wiki_pattern_extractor = WikipediaPatternExtractor.from_config_file()

    # preprocess data
    wiki_pattern_extractor.discover_patterns()
    wiki_pattern_extractor.extract_patterns()

    # print Part-of-speech tagged sentences
    wiki_pattern_extractor.print_occurences()

    wiki_pattern_extractor.merge_patterns()
    wiki_pattern_extractor.clean_patterns()
    wiki_pattern_extractor.save_patterns()

    # calculate occured facts coverage
    wiki_pattern_extractor.calculate_text_coverage()