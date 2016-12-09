#!../venv/bin/python
# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------------------------------
#                               Imports
# -------------------------------------------------------------------------------------------------

from __future__ import division
from termcolor import colored
from bs4 import BeautifulSoup as bs
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.tag import pos_tag_sents
from nltk.corpus import treebank
from copy import deepcopy
from ascii_graph import Pyasciigraph
import re
import sys
import csv
from random import randint
import imp
from tqdm import tqdm
import pickle
import itertools

import pattern_extractor
from pattern_extractor import Pattern

wikipedia_connector = imp.load_source('wikipedia_connector', '../wikipedia connector/wikipedia_connector.py')
from wikipedia_connector import WikipediaConnector


class WikiPatternExtractor(object):
    def __init__(self, limit, resources_path='../ttl parser/mappingbased_objects_en_extracted.csv',
                 relationships=[], use_dump=False, randomize=False, perform_tests=False,
                 write_path='../data/patterns.pkl'):
        self.resources_path = resources_path
        self.use_dump = use_dump
        self.relationships = ['http://dbpedia.org/ontology/' + r for r in relationships if r]
        self.limit = limit
        self.dbpedia = {}
        self.relation_patterns = {}
        self.randomize = randomize
        self.perform_tests = perform_tests
        self.write_path = write_path
        self.wikipedia_connector = WikipediaConnector(self.use_dump)

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
                random_offset = randint(0, 10000)
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
        """ Returns cleaned sentences which contain any of given Wikipedia resources """
        # sentences = sent_tokenize(text)
        relevant_sentences = filter(lambda sent: self.wikipedia_connector.contains_any_reference(sent.as_string(), wikipedia_resources),
                                    tagged_sentences)
        # relevant_sentences = map(self.clean_tags, relevant_sentences)
        return relevant_sentences

    def shorten_sentence(self, items):
        """
        Takes [entity, relation, resource, sentence] list and crops the
        sentence after the last appearance of the target resource.
        Returns [entity, relation, resource, shortened_sentence] list
        """
        entity, relation, resource, sentence = items
        shortened_sentence = ' '.join(sentence.split(resource)[:-1]) + ' ' + resource
        return [entity, relation, resource, shortened_sentence]

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

        print('Sentence Extraction...')
        for entity, values in tqdm(self.dbpedia.iteritems(), total=len(self.dbpedia)):
            # fetch corresponding wiki article
            html_text = self.wikipedia_connector.get_wikipedia_article(entity)

            # for each relationship filter sentences that contain
            # target resources of entity's relationship
            for rel, resources in values.iteritems():
                wikipedia_target_resources = map(self.wikipedia_connector.wikipedia_uri, resources)
                # DBP_target_resources = map(self.normalize_DBP_uri, resources)
                sentences = self.wikipedia_connector.html_sent_tokenize(html_text)
                tagged_sentences = self.wikipedia_connector.make_to_tagged_sentences(sentences)
                relevant_sentences = self.filter_relevant_sentences(tagged_sentences, wikipedia_target_resources)
                values[rel] = {'resources': wikipedia_target_resources,
                               'sentences': relevant_sentences}
        print

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

        print('Pattern extraction...')
        for entity, relations in tqdm(self.dbpedia.iteritems(), total=len(self.dbpedia)):
            for rel_ontology, values in relations.iteritems():
                target_resources = values['resources']
                sentences = values['sentences']
                entity = self.wikipedia_connector.normalize_uri(entity)
                rel_ontology = rel_ontology.split('/')[-1]
                data = [[entity, rel_ontology, res, sent]
                        for res in target_resources
                        for sent in sentences
                        if self.wikipedia_connector.contains_any_reference(sent.as_string(), [res]) and res != entity]
                # remove needless sentence information based on relation facts
                # data = map(self.shorten_sentence, data)
                # POS tag sentences
                for entry in data:
                    sentence = entry[3]
                    resource = entry[2]
                    relative_position = sentence.calculate_relative_position()
                    soup = bs(sentence.as_string(), 'lxml')
                    nl_sentence = soup.get_text()
                    entry.append(nl_sentence)
                    tokenized_sentences = map(word_tokenize, [nl_sentence])
                    pos_tagged_sentences = pos_tag_sents(tokenized_sentences).pop()
                    object_tokens = self.wikipedia_connector.find_tokens_in_html(sentence.as_string(), resource)
                    pattern = pattern_extractor.extract_pattern(nl_sentence, object_tokens, relative_position)
                    if pattern is not None:
                        values['pattern'] = pattern
                        entry.append(pattern)

                    # color sentence parts according to POS tag
                    colored_sentence = [colored(word, color_mapping.setdefault(pos, 'white'))
                                        for word, pos in pos_tagged_sentences]
                    colored_sentence = ' '.join(colored_sentence)
                    colored_sentence = re.sub(r' (.\[\d+m),', ',', colored_sentence)  # remove space before commas
                    entry.append(colored_sentence)

                results.extend(data)
        print

        # drop duplicates
        results.sort()
        results = list(x for x, _ in itertools.groupby(results))

        # print results
        # 0 -> entity  1 -> relationship 2 -> target resource 3 -> sentence
        for entry in results:
            '''print(colored('[DBP Entitity] \t', 'red',
                          attrs={'concealed', 'bold'}) + colored(entry[0], 'white')).expandtabs(20)
            print(colored('[DBP Ontology] \t', 'red',
                          attrs={'concealed', 'bold'}) + colored(entry[1], 'white')).expandtabs(20)
            print(colored('[DBP Resource] \t', 'red',
                          attrs={'concealed', 'bold'}) + colored(self.wikipedia_connector.normalize_uri(entry[2]), 'white')).expandtabs(20)
            print(colored('[Wiki Occurence] \t',
                          'red', attrs={'concealed', 'bold'}) + entry[6]).expandtabs(20)'''

            # print(entry[5])
            '''print(colored('[Pattern] \t',
                          'red', attrs={'concealed', 'bold'}) + colored(entry[5], 'white')).expandtabs(20)
            print(colored('[Pattern] \t',
                          'red', attrs={'concealed', 'bold'}) + colored(entry[6], 'white')).expandtabs(20)'''
            print('')

        print('[POS KEY]\t'
              + colored('NORMAL NOUN\t', 'magenta')
              + colored('PROPER NOUN\t', 'green')
              + colored('VERB\t', 'cyan')
              + colored('ADJ\t', 'yellow')).expandtabs(20)

    def count_occurences(self, values, sentences):
        """ Self-explanatory """
        total_count, occured_count = 0, 0
        for val in values:
            total_count += 1
            if val in ' '.join(sentences):
                occured_count += 1

        return total_count, occured_count

    def calculate_text_coverage(self):
        """ Prints CLI stats about percentage of matched dbpedia facts in wiki raw text.  """
        occurence_count = {}
        for entity, relationships in self.dbpedia.iteritems():
            for rel, values in relationships.iteritems():
                target_resources = values.get('resources', [])
                sentences = map(lambda sent: sent.as_string(), values.get('sentences', []))
                total_facts, occured_facts = self.count_occurences(target_resources, sentences)
                relation_count = occurence_count.setdefault(rel, {'total': 0, 'matched': 0})
                relation_count['total'] += total_facts
                relation_count['matched'] += occured_facts

        # print bar chart
        num_rel = len(occurence_count)
        data = [('%  ' + str(vals['matched']) + '/' + str(vals['total']) + ' ' + rel.split('/')[-1],
                 vals['matched'] / vals['total'] * 100)
                for rel, vals in occurence_count.iteritems()]
        graph = Pyasciigraph()
        for line in graph.graph('occured facts in percentage', data):
            print(line)

    def merge_patterns(self):
        print('Pattern merging...')
        for entity, relations in tqdm(self.dbpedia.iteritems(), total=len(self.dbpedia)):
            for rel, values in relations.iteritems():
                if 'pattern' not in values.keys():
                    continue
                pattern = values['pattern']
                if rel in self.relation_patterns.keys():
                    self.relation_patterns[rel] = Pattern.merge(self.relation_patterns[rel], pattern,
                                                                self.perform_tests)
                else:
                    self.relation_patterns[rel] = pattern
        print

    def save_patterns(self):
        with open(self.write_path, 'wb') as fout:
            output = (self.dbpedia.keys(), self.relation_patterns)
            pickle.dump(output, fout, pickle.HIGHEST_PROTOCOL)


def parse_input_parameters():
    use_dump, randomize, perform_tests = False, False, True
    helped = False

    for arg in sys.argv[1:]:
        if arg == '--dump':
            use_dump = True
        elif arg == '--rand':
            randomize = True
        elif arg == '--test':
            perform_tests = True
        elif not helped:
            print 'Usage: python wiki_pattern.py [--dump] [--rand] [--test]'
            helped = True

    return use_dump, randomize, perform_tests


if __name__ == '__main__':
    use_dump, randomize, perform_tests = parse_input_parameters()
    wiki = WikiPatternExtractor(1000, use_dump=use_dump, randomize=randomize, perform_tests=perform_tests)
    # preprocess data
    wiki.discover_patterns()
    # print Part-of-speech tagged sentences
    wiki.print_patterns()
    # calculate occured facts coverage
    wiki.calculate_text_coverage()

    wiki.merge_patterns()
    wiki.save_patterns()
