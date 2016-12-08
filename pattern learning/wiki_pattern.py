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
import requests
import csv
import itertools
from timeit import default_timer as timer
from random import randint
import imp
from tqdm import tqdm
import pickle

import pattern_extractor
from pattern_extractor import Pattern
from tagged_sentence import TaggedSentence

redirector = imp.load_source('subst_redirects', '../data cleaning/subst_redirects.py')
dump_extractor = imp.load_source('dump_extractor', '../wikipedia dump connector/dump_extractor.py')


class WikiPatternExtractor(object):
    def __init__(self, limit_training, limit_discovery, path='../ttl parser/mappingbased_objects_en_extracted.csv',
                 relationships=[], use_dump=False, randomize=False, perform_tests=False, match_threshold=0.01,
                 redirects_path='../data/redirects_en.txt'):
        self.path = path
        self.use_dump = use_dump
        self.relationships = ['http://dbpedia.org/ontology/' + r for r in relationships if r]
        self.limit_training = limit_training
        self.limit_discovery = limit_discovery
        self.dbpedia = {}
        self.relation_patterns = {}
        self.elapsed_time = 0  # for performance monitoring
        self.randomize = randomize
        self.perform_tests = perform_tests
        self.fact_discovery_resources = set()
        self.match_threshold = match_threshold
        self.patterns_file = '../data/patterns.pkl'
        if use_dump:
            self.redirector = False
        else:
            self.redirector = redirector.Substitutor(redirects_path)

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

            if self.randomize:
                random_offset = randint(0, 10000)
                for row in wikireader:
                    random_offset -= 1
                    if random_offset == 0:
                        break

            max_results = self.limit_training
            for row in wikireader:
                if max_results == 0:
                    break
                subject, relation, value = row[0], row[1], row[2]
                # maintain a dict for each entity with given relations as key
                # and their target values as list
                entities.setdefault(subject, {}).setdefault(relation, []).append(value)
                max_results -= 1

            max_results = self.limit_discovery
            for row in wikireader:
                if max_results == 0:
                    break
                subject = row[0]
                if subject not in entities.keys() and subject not in self.fact_discovery_resources:
                    self.fact_discovery_resources.add(subject)
                    max_results -= 1
        return entities

    def scrape_wikipedia_article(self, dbpedia_resource):
        """
        Requests wikipedia resource per GET request - extracts text content
        and returns text
        """
        # http://dbpedia.org/resource/Alain_Connes -> http://en.wikipedia.org/wiki/Alain_Connes
        wiki_url = dbpedia_resource.replace("dbpedia.org/resource", "en.wikipedia.org/wiki")

        response = requests.get(wiki_url)
        article = response.content.decode('utf-8')
        return article

    def get_wikipedia_article(self, dbpedia_resource):
        start = timer()
        if self.use_dump:
            resource = self.normalize_uri(dbpedia_resource)
            article = dump_extractor.get_wikipedia_html_from_dump(resource)
        else:
            article = self.scrape_wikipedia_article(dbpedia_resource)
        end = timer()
        self.elapsed_time += end - start
        soup = bs(article, 'lxml')
        text = soup.find_all('p')
        return text

    def normalize_uri(self, uri):
        """
        http://dbpedia.org/resource/Alain_Connes -> 'Alain Connes'
        """
        name = uri.split('/')[-1].replace('_', ' ')
        return self.__cleanInput(name)

    def wikipedia_uri(self, DBP_uri):
        return DBP_uri.replace("http://dbpedia.org/resource/", "/wiki/")

    def __cleanInput(self, input):
        """
        Sanitize text - remove multiple new lines and spaces - get rid of non ascii chars
        and citations - strip words from punctuation signs - returns sanitized string
        """
        input = re.sub(r'\n+', " ", input)
        input = re.sub(r' +', " ", input)
        input = input.replace("\'", "")

        # substitute redirects
        if self.redirector:
            input = self.redirector.substitute_all(input)

        # get rid of non-ascii characters
        input = re.sub(r'[^\x00-\x7f]', r'', input)

        # get rid of citations
        input = re.sub(r'\[\d+\]', r'', input)
        cleanInput = []
        input = input.split(' ')
        for item in input:
            # item = item.strip('?!;,')
            if len(item) > 1 or (item.lower() == 'a' or item == 'I'):
                cleanInput.append(item)
        return ' '.join(cleanInput).encode('utf-8')  # ' '.join(cleanInput).lower().encode('utf-8')

    def splitkeepsep(self, s, sep):
        """ http://programmaticallyspeaking.com/split-on-separator-but-keep-the-separator-in-python.html """
        return reduce(lambda acc, elem: acc[:-1] + [acc[-1] + elem] if elem == sep else acc + [elem],
                      re.split("(%s)" % re.escape(sep), s), [])

    @staticmethod
    def has_appropriate_text_length(html):
        soup = bs(html, 'lxml')
        length = len(soup.get_text())
        return 0 < length < 200

    def html_sent_tokenize(self, paragraphs):
        # TODO: improve so that valid html comes out, issue #18
        sentences = []
        for p in paragraphs:
            sentences.extend(self.splitkeepsep(p.prettify(), '.'))
        sentences = map(self.__cleanInput, sentences)
        sentences = filter(WikiPatternExtractor.has_appropriate_text_length, sentences)
        return sentences

    def clean_tags(self, html_text):
        # html_text = re.sub(r'<[^a].*?>', '', html_text) # Intention: Only keep <a></a> Tags. Problem: Deletes </a> tags.
        html_text = '<p>' + html_text + '</p>'
        return html_text

    def contains_any_reference(self, html, resources=None):
        soup = bs(html, 'lxml')
        if resources is None:
            return soup.find('a')
        else:
            return any(soup.find('a', {'href': resource}) for resource in resources)

    def make_to_tagged_sentences(self, sentences):
        article_length = len(sentences)
        for i in range(0, article_length):
            sentences[i] = TaggedSentence(sentences[i], i, article_length)
        return sentences

    def filter_relevant_sentences(self, tagged_sentences, wikipedia_resources):
        """ Returns cleaned sentences which contain any of given Wikipedia resources """
        # sentences = sent_tokenize(text)
        relevant_sentences = filter(lambda sent: self.contains_any_reference(sent.as_string(), wikipedia_resources),
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

        print('Collecting training data...')
        for entity, values in tqdm(self.dbpedia.iteritems(), total=len(self.dbpedia)):
            # fetch corresponding wiki article
            html_text = self.get_wikipedia_article(entity)

            # for each relationship filter sentences that contain
            # target resources of entity's relationship
            for rel, resources in values.iteritems():
                wikipedia_target_resources = map(self.wikipedia_uri, resources)
                # DBP_target_resources = map(self.normalize_DBP_uri, resources)
                sentences = self.html_sent_tokenize(html_text)
                tagged_sentences = self.make_to_tagged_sentences(sentences)
                relevant_sentences = self.filter_relevant_sentences(tagged_sentences, wikipedia_target_resources)
                values[rel] = {'resources': wikipedia_target_resources,
                               'sentences': relevant_sentences}
        print

    # ---------------------------------------------------------------------------------------------
    #                               Statistics and Visualizations
    # ---------------------------------------------------------------------------------------------

    def find_tokens_in_html(self, html, resource):
        soup = bs(html, 'lxml')
        reference = soup.find('a', {'href': resource})
        reference_text = reference.get_text()
        return word_tokenize(reference_text)

    def find_tokens_of_references_in_html(self, html):
        soup = bs(html, 'lxml')
        references = soup.findAll('a')
        references = map(lambda ref: (ref['href'], ref.get_text()), references)
        references = map(lambda (href, text): (href, word_tokenize(text)), references)
        assert len(references) > 0
        return references

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

        print('Extracting patterns for training...')
        for entity, relations in tqdm(self.dbpedia.iteritems(), total=len(self.dbpedia)):
            for rel_ontology, values in relations.iteritems():
                target_resources = values['resources']
                sentences = values['sentences']
                entity = self.normalize_uri(entity)
                rel_ontology = rel_ontology.split('/')[-1]
                data = [[entity, rel_ontology, res, sent]
                        for res in target_resources
                        for sent in sentences
                        if self.contains_any_reference(sent.as_string(), [res]) and res != entity]
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
                    object_tokens = self.find_tokens_in_html(sentence.as_string(), resource)
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

        """"# drop duplicates
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
                          attrs={'concealed', 'bold'}) + colored(self.normalize_uri(entry[2]), 'white')).expandtabs(20)
            print(colored('[Wiki Occurence] \t',
                          'red', attrs={'concealed', 'bold'}) + entry[6]).expandtabs(20)

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
              + colored('ADJ\t', 'yellow')).expandtabs(20)"""

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

    def get_elapsed_time(self):
        return self.elapsed_time

    def merge_patterns(self):
        print('Training patterns...')
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
            object_tokens_of_references = self.find_tokens_of_references_in_html(sent.as_string())
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

    def discover_new_facts(self):
        facts = []
        print('Discovering new facts...')
        for resource in self.fact_discovery_resources:
            print('--- ' + resource + ' ----')
            html_text = self.get_wikipedia_article(resource)
            sentences = self.html_sent_tokenize(html_text)
            tagged_sentences = self.make_to_tagged_sentences(sentences)
            referenced_sentences = filter(lambda sent: self.contains_any_reference(sent.as_string()), tagged_sentences)
            new_facts = self.discover_facts_in_sentences(referenced_sentences)
            new_facts = [(resource, rel, obj, score, nl_sentence) for (rel, obj, score, nl_sentence) in new_facts]
            facts.extend(new_facts)

        print('\n----- Discovered facts ------')
        for fact in facts:
            print fact

    '''def save_patterns(self):
        with open(self.patterns_file) as fin:



    def load_patterns(self):
        pass'''


def parse_input_parameters():
    use_dump, randomize, perform_tests = True, False, True
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
    wiki = WikiPatternExtractor(200, 20, use_dump=use_dump, randomize=randomize, perform_tests=perform_tests)
    # preprocess data
    wiki.discover_patterns()
    # print Part-of-speech tagged sentences
    wiki.print_patterns()
    # calculate occured facts coverage
    wiki.calculate_text_coverage()

    wiki.merge_patterns()
    wiki.discover_new_facts()
