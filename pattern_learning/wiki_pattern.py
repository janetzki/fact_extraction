#!../venv/bin/python
# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------------------------------
#                               Imports
# -------------------------------------------------------------------------------------------------

from __future__ import division
from termcolor import colored
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag_sents
from ascii_graph import Pyasciigraph
import re
import csv
from random import randint
import imp
from tqdm import tqdm
import pickle
import itertools

from pattern_extractor import PatternExtractor, Pattern

wikipedia_connector = imp.load_source('wikipedia_connector', '../wikipedia_connector/wikipedia_connector.py')
from wikipedia_connector import WikipediaConnector
from ConfigParser import SafeConfigParser


class WikiPatternExtractor(object):
    def __init__(self, limit, resources_path='../data/mappingbased_objects_en_filtered.csv',
                 relationships=[], use_dump=False, randomize=False, perform_tests=False,
                 write_path='../data/patterns.pkl', replace_redirects=False):
        self.resources_path = resources_path
        self.use_dump = use_dump
        self.relationships = ['http://dbpedia.org/ontology/' + r for r in relationships if r]
        self.limit = limit
        self.dbpedia = {}
        self.relation_patterns = {}
        self.randomize = randomize
        self.perform_tests = perform_tests
        self.write_path = write_path
        self.wikipedia_connector = WikipediaConnector(use_dump=self.use_dump, redirect=replace_redirects)
        self.pattern_extractor = PatternExtractor()

    # -------------------------------------------------------------------------------------------------
    #                               Data Preprocessing
    # -------------------------------------------------------------------------------------------------

    def filter_DBpedia_data(self, relationships):
        pass  # TODO:

    def parse_DBpedia_data(self):
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
        with open(self.resources_path, 'r') as f:
            wikireader = csv.reader(f, delimiter=' ', quotechar='"')

            if self.randomize:
                random_offset = randint(0, 10000)  # TODO: get rid off magic number
                for row in wikireader:
                    random_offset -= 1
                    if random_offset == 0:
                        break

            max_results = self.limit
            for row in wikireader:
                if max_results == 0:
                    break
                subject, relation, value = row[0], row[1], row[2]
                # maintain a dict for each entity with given relations as key
                # and their target values as list
                entities.setdefault(subject, {}).setdefault(relation, []).append(value)
                max_results -= 1
        return entities

    def filter_relevant_sentences(self, tagged_sentences, wikipedia_resources):
        """ Returns sentences which contain any of given Wikipedia resources """
        return filter(lambda sent: sent.contains_any_link(wikipedia_resources), tagged_sentences)

    def discover_patterns(self, relationships=[]):
        """
        Preprocesses data (initializing main data structure)
        1. Filter relevant DBpedia facts by relationships -> still TODO
        2. Turn DBpedia data into in-memory dictionary where all processing takes place
        3. Fetch relevant Wikipedia articles and filter relevant sentences out of html text (for link search)
        4. Data is stored in self.dbpedia
        """
        # filter dbpedia dataset for relevant relationships - still TODO
        self.filter_DBpedia_data(relationships)

        # parse dbpedia information
        self.dbpedia = self.parse_DBpedia_data()

        tqdm.write('\n\nSentence extraction...')
        for entity, values in tqdm(self.dbpedia.iteritems(), total=len(self.dbpedia)):
            tagged_sentences = self.wikipedia_connector.get_parsed_wikipedia_article(entity)

            # for each relationship filter sentences that contain
            # target resources of entity's relationship
            for rel, resources in values.iteritems():
                wikipedia_target_resources = map(WikipediaConnector.convert_to_wikipedia_uri, resources)
                relevant_sentences = self.filter_relevant_sentences(tagged_sentences, wikipedia_target_resources)
                values[rel] = {'resources': wikipedia_target_resources,
                               'sentences': relevant_sentences,
                               'patterns': []}

    # ---------------------------------------------------------------------------------------------
    #                               Statistics and Visualizations
    # ---------------------------------------------------------------------------------------------

    def print_patterns(self):
        """
        Prints each occurence of a given DBpedia fact with their corresponding and matched sentence.
        The matched sentence is POS tagges using maxent treebank pos tagging model.
        Nouns, verbs and adjectives are printed in colour.
        """
        color_mapping = {
            'magenta': ['NN', 'NNS'],
            'green': ['NNP', 'NNPS'],
            'cyan': ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ'],
            'yellow': ['JJ', 'JJR', 'JJS']
        }
        # reverse color mapping
        color_mapping = {v: k for k, values in color_mapping.iteritems() for v in values}

        # build table data
        results = []
        # corpus = deepcopy(self.dbpedia)

        tqdm.write('\n\nPattern extraction...')
        for entity, relations in tqdm(self.dbpedia.iteritems(), total=len(self.dbpedia)):
            cleaned_subject_entity_name = self.wikipedia_connector.strip_cleaned_entity_name(entity)
            subject_entity = self.wikipedia_connector.strip_entity_name(entity)
            for rel_ontology, values in relations.iteritems():
                target_resources = values['resources']
                sentences = values['sentences']
                rel_ontology = rel_ontology.split('/')[-1]
                data = [{'entity': cleaned_subject_entity_name, 'relation': rel_ontology, 'resource': res, 'sentence': sent}
                        for res in target_resources
                        for sent in sentences
                        if sent.contains_any_link([res]) and res != entity]

                # remove needless sentence information based on relation facts
                # data = map(self.shorten_sentence, data)
                # POS tag sentences
                for entry in data:
                    sentence = entry['sentence']
                    resource = entry['resource']
                    nl_sentence = sentence.as_string()
                    relative_position = sentence.relative_pos
                    entry['nl sentence'] = nl_sentence
                    tokenized_sentences = map(word_tokenize, [nl_sentence])
                    pos_tagged_sentences = pos_tag_sents(tokenized_sentences).pop()

                    object_addresses = sentence.addresses_of_link(resource)
                    object_entity = WikipediaConnector.strip_entity_name(resource)
                    pattern = self.pattern_extractor.extract_pattern(nl_sentence, object_addresses, relative_position,
                                                                     subject_entity, object_entity)

                    if pattern is not None:
                        values['patterns'].append(pattern)
                        entry['pattern'] = pattern

                    # color sentence parts according to POS tag
                    colored_sentence = [colored(word, color_mapping.setdefault(pos, 'white'))
                                        for word, pos in pos_tagged_sentences]
                    colored_sentence = ' '.join(colored_sentence)
                    colored_sentence = re.sub(r' (.\[\d+m),', ',', colored_sentence)  # remove space before commas
                    entry['colored sentence'] = colored_sentence

                results.extend(data)

        # drop duplicates
        results.sort()
        results = list(x for x, _ in itertools.groupby(results))

        for entry in results:
            print(colored('[DBP Entitity] \t', 'red',
                          attrs={'concealed', 'bold'}) + colored(entry['entity'], 'white')).expandtabs(20)
            print(colored('[DBP Ontology] \t', 'red',
                          attrs={'concealed', 'bold'}) + colored(entry['relation'], 'white')).expandtabs(20)
            print(colored('[DBP Resource] \t', 'red',
                          attrs={'concealed', 'bold'}) + colored(
                self.wikipedia_connector.strip_cleaned_entity_name(entry['resource']),
                'white')).expandtabs(20)
            print(colored('[Wiki Occurence] \t',
                          'red', attrs={'concealed', 'bold'}) + entry['colored sentence']).expandtabs(20)
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
            self.relation_patterns[relation] = Pattern.clean_pattern(pattern)
        self.relation_patterns = dict(filter(lambda (rel, pat): pat is not None, self.relation_patterns.iteritems()))

    def save_patterns(self):
        print('\n\nPattern saving...')
        with open(self.write_path, 'wb') as fout:
            output = self.dbpedia.keys(), self.relation_patterns
            pickle.dump(output, fout, pickle.HIGHEST_PROTOCOL)


def get_input_parameters_from_file(path):
    config = SafeConfigParser()
    config.read(path)
    use_dump = config.getboolean('general', 'use_dump')
    randomize = config.getboolean('wiki_pattern', 'randomize')
    perform_tests = config.getboolean('wiki_pattern', 'randomize')
    limit = config.getint('wiki_pattern', 'limit')
    replace_redirects = config.getboolean('wiki_pattern', 'replace_redirects')
    return use_dump, randomize, perform_tests, limit, replace_redirects


if __name__ == '__main__':
    use_dump, randomize, perform_tests, limit, replace_redirects = get_input_parameters_from_file('../config.ini')
    wiki = WikiPatternExtractor(limit, use_dump=use_dump, randomize=randomize, perform_tests=perform_tests,
                                replace_redirects=replace_redirects)

    # preprocess data
    wiki.discover_patterns()
    # print Part-of-speech tagged sentences
    wiki.print_patterns()
    wiki.merge_patterns()
    wiki.clean_patterns()
    wiki.save_patterns()

    # calculate occured facts coverage
    wiki.calculate_text_coverage()
