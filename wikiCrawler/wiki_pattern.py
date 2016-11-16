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
from copy import deepcopy
from ascii_graph import Pyasciigraph
import re
import sys
import requests
import csv
import itertools


class WikiPatternExtractor(object):
    def __init__(self, path='../ttl parser/mappingbased_objects_en_extracted.csv', \
                 relationships=[], limit=500):
        self.path = path
        self.relationships = ['http://dbpedia.org/ontology/' + r for r in relationships if r]
        self.limit = limit
        self.dbpedia = {}
        self.relationship_patterns = {}

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
        with open(self.path, 'r') as f:
            wikireader = csv.reader(f, delimiter=' ', quotechar='"')
            max_results = self.limit
            for row in wikireader:
                if max_results is 0:
                    break
                subject, relation, value = row[0], row[1], row[2]
                # maintain a dict for each entity with given relations as key
                # and their target values as list
                entities.setdefault(subject, {}).setdefault(relation, []).append(value)
                max_results -= 1
        return entities

    def scrape_wikipedia_article(self, dbpedia_resource):
        """
        Requests wikipedia resource per GET request - extracts text content
        and returns sanitized text
        """
        # http://dbpedia.org/resource/Alain_Connes -> http://en.wikipedia.org/wiki/Alain_Connes
        wiki_url = dbpedia_resource.replace("dbpedia.org/resource", "en.wikipedia.org/wiki")
        response = requests.get(wiki_url)
        article = response.content.decode('utf-8')
        soup = bs(article, 'lxml')
        # text = [p.get_text() for p in soup.find_all('p')]
        # self.__cleanInput(' '.join(text))
        text = soup.find_all('p')
        return text

    def normalize_DBP_uri(self, uri):
        """
        #http://dbpedia.org/resource/Alain_Connes -> 'alain connes'
        http://dbpedia.org/resource/Alain_Connes -> '/wiki/Alian_Connes'
        """
        name = uri.split('/')[-1].replace('_', ' ')  # .lower()
        return self.__cleanInput(name)

    def wikipedia_uri(self, DBP_uri):
        return DBP_uri.replace("http://dbpedia.org/resource/", "/wiki/")

    def __cleanInput(self, input):
        """
        Sanitize text - remove multiple new lines and spaces - get rid of non ascii chars
        and citations - strip words from punctuation signs - returns sanitized string
        """
        input = re.sub('\n+', " ", input)
        input = re.sub(' +', " ", input)

        # get rid of non-ascii characters
        input = re.sub(r'[^\x00-\x7f]', r'', input)

        # get rid of citations
        input = re.sub(r'\[\d+\]', r'', input)
        cleanInput = []
        input = input.split(' ')
        for item in input:
            item = item.strip('?!;,')
            if len(item) > 1 or (item.lower() == 'a' or item.lower() == 'i'):
                cleanInput.append(item)
        return ' '.join(cleanInput).encode('utf-8')  # ' '.join(cleanInput).lower().encode('utf-8')

    def splitkeepsep(self, s, sep):
        """ http://programmaticallyspeaking.com/split-on-separator-but-keep-the-separator-in-python.html """
        return reduce(lambda acc, elem: acc[:-1] + [acc[-1] + elem] if elem == sep else acc + [elem],
                      re.split("(%s)" % re.escape(sep), s), [])

    def html_sent_tokenize(self, paragraphs):
        sentences = []
        for p in paragraphs:
            sentences.extend(self.splitkeepsep(p.prettify(), '.'))
        return sentences

    def remove_tags(self, html_text):
        return re.sub(r'<.*?>', '', html_text)

    def filter_relevant_sentences(self, paragraphs, wikipedia_resources):
        """ Returns cleaned sentences which contain any of given Wikipedia resources """
        # sentences = sent_tokenize(text)
        sentences = self.html_sent_tokenize(paragraphs)
        sentences = map(self.__cleanInput, sentences)
        relevant_sentences = filter(lambda s: any(resource in s for resource in wikipedia_resources), sentences)
        relevant_sentences = map(self.remove_tags, relevant_sentences)
        return relevant_sentences

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

        for entity, values in self.dbpedia.iteritems():
            # fetch corresponding wiki article
            html_text = self.scrape_wikipedia_article(entity)

            # for each relationship filter sentences that contain
            # target resources of entity's relationship
            for rel, resources in values.iteritems():
                wikipedia_target_resources = map(self.wikipedia_uri, resources)
                DBP_target_resources = map(self.normalize_DBP_uri, resources)
                relevant_sentences = self.filter_relevant_sentences(html_text, wikipedia_target_resources)
                values[rel] = {'resources': DBP_target_resources,
                               'sentences': relevant_sentences}

    # ---------------------------------------------------------------------------------------------
    #                               Statistics and Visualizations
    # ---------------------------------------------------------------------------------------------

    def print_pos_tagged_sentences(self):
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
        corpus = deepcopy(self.dbpedia)

        for entity, relations in corpus.iteritems():
            for rel_ontology, values in relations.iteritems():
                target_resources = values['resources']
                sentences = values['sentences']
                entity = self.normalize_DBP_uri(entity)
                rel_ontology = rel_ontology.split('/')[-1]
                data = [[entity, rel_ontology, res, sent]
                        for res in target_resources
                        for sent in sentences
                        if res in sent and res != entity]
                # POS tag sentences
                for entry in data:
                    sentence = entry[3]
                    tokenized_sentences = map(word_tokenize, [sentence])
                    pos_tagged_sentences = pos_tag_sents(tokenized_sentences).pop()
                    # color sentence parts according to POS tag
                    colored_sentence = [colored(word, color_mapping.setdefault(pos, 'white'))
                                        for word, pos in pos_tagged_sentences]
                    entry[3] = ' '.join(colored_sentence)

                results.extend(data)

        # drop duplicates
        results.sort()
        results = list(x for x, _ in itertools.groupby(results))

        # print results
        # 0 -> entity  1 -> relationship 2 -> target resource 3 -> sentence
        for entry in results:
            print(colored('[DBP Entitity] \t', 'red',
                          attrs={'concealed', 'bold'}) + colored(entry[0], 'white')).expandtabs(20)
            print(colored('[DBP Ontology] \t', 'red',
                          attrs={'concealed', 'bold'}) + colored(entry[1], 'white')).expandtabs(20)
            print(colored('[DBP Resource] \t', 'red',
                          attrs={'concealed', 'bold'}) + colored(entry[2], 'white')).expandtabs(20)
            print(colored('[Wiki Occurence] \t',
                          'red', attrs={'concealed', 'bold'}) + entry[3] + '\n').expandtabs(20)

        print('[KEY]\t'
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
                sentences = values.get('sentences', [])
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


if __name__ == '__main__':
    wiki = WikiPatternExtractor(limit=100)
    # preprocess data
    wiki.discover_patterns()
    # print Part-of-speech tagged sentences
    wiki.print_pos_tagged_sentences()
    # calculate occured facts coverage
    wiki.calculate_text_coverage()
