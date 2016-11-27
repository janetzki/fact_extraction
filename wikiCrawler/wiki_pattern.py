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
from pattern.en import parsetree
import re
import sys
import requests
import csv
import itertools
from timeit import default_timer as timer
import pattern_extractor


class WikiPatternExtractor(object):
    def __init__(self, path='../ttl parser/mappingbased_objects_en_extracted.csv', \
                 relationships=[], limit=500, use_dump=False,
                 dump_path='../data/enwiki-latest-pages-articles.xml'):
        self.path = path
        self.use_dump = use_dump
        self.dump_path = dump_path
        self.relationships = ['http://dbpedia.org/ontology/' + r for r in relationships if r]
        self.limit = limit
        self.dbpedia = {}
        self.relationship_patterns = {}
        self.elapsed_time = 0  # for performance monitoring

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

    def get_dump_offset_via_index(self, title):
        index_path = '../data/index.csv'
        with open(index_path, 'r') as fin:
            indexreader = csv.reader(fin, delimiter='#')
            for line in indexreader:
                if line[0] == title:
                    fin.close()
                    return int(line[1])
            fin.close()
        return -1

    def extract_wikipedia_page_via_offset(self, offset, dump_path):
        with open(dump_path, 'r') as fin:
            fin.seek(offset)
            text = "  <page>\n"
            for line in fin:
                text += line
                if line[0:9] == "  </page>":
                    break
            return text

    def extract_wikipedia_text_from_page(self, page):
        soup = bs(page, 'lxml')
        return soup.find('text').get_text()

    def replace_links(self, match):
        resource, text = match.groups()
        if text == "":
            text = resource
        resource = resource.replace(' ', '_')
        html_link = '<a href="/wiki/' + resource + '">' + text + '</a>'
        return html_link

    def strip_outer_brackets(self, text):
        # http://stackoverflow.com/questions/14596884/remove-text-between-and-in-python
        stripped = ''
        skip = 0
        for i in text:
            if i == '{':
                skip += 1
            elif i == '}' and skip > 0:
                skip -= 1
            elif skip == 0:
                stripped += i
        return stripped

    def make_wikipedia_text_to_html(self, text):
        """ No perfect HTML - just for unified processing, e.g., link search """
        # drop infobox and other garbage inside {...}
        html_text = self.strip_outer_brackets(text)

        # remove all headlines
        html_text = re.sub(r'(=+).*?(\1)', '', html_text)
        html_text = re.sub(r"'''.*?'''", '', html_text)

        html_text = re.sub(r'\[\[Category:.*\]\]', '', html_text)
        html_text = re.sub(r'\[http://.*?\]', '', html_text)  # drop hyperlinks
        html_text = re.sub(r'\* ?', '', html_text)

        # insert HTML links
        rx_references = re.compile(r'\[\[([^\|\]]*)\|?(.*?)\]\]')
        html_text = re.sub(rx_references, self.replace_links, html_text)
        return html_text

    def get_wikipedia_html_from_dump(self, dbpedia_resource):
        resource = self.normalize_uri(dbpedia_resource)
        offset = self.get_dump_offset_via_index(resource)
        if offset < 0:
            return ''  # no article found, resource probably contains non-ASCII character TODO: Heed this case.
        page = self.extract_wikipedia_page_via_offset(offset, self.dump_path)
        text = self.extract_wikipedia_text_from_page(page)
        html_text = self.make_wikipedia_text_to_html(text)
        return html_text

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
            article = self.get_wikipedia_html_from_dump(dbpedia_resource)
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
        input = re.sub('\n+', " ", input)
        input = re.sub(' +', " ", input)

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

    def html_sent_tokenize(self, paragraphs):
        # TODO: improve so that valid html comes out
        sentences = []
        for p in paragraphs:
            sentences.extend(self.splitkeepsep(p.prettify(), '.'))
        return sentences

    def clean_tags(self, html_text):
        # html_text = re.sub(r'<[^a].*?>', '', html_text) # Intention: Only keep <a></a> Tags. Problem: Deletes </a> tags.
        html_text = '<p>' + html_text + '</p>'
        return html_text

    def contains_any_reference(self, html, resources):
        soup = bs(html, 'lxml')
        return any(soup.find('a', {'href': resource}) for resource in resources)

    def filter_relevant_sentences(self, paragraphs, wikipedia_resources):
        """ Returns cleaned sentences which contain any of given Wikipedia resources """
        # sentences = sent_tokenize(text)
        sentences = self.html_sent_tokenize(paragraphs)
        sentences = map(self.__cleanInput, sentences)
        relevant_sentences = filter(lambda sent: self.contains_any_reference(sent, wikipedia_resources), sentences)
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

        for entity, values in self.dbpedia.iteritems():
            # fetch corresponding wiki article
            html_text = self.get_wikipedia_article(entity)

            # for each relationship filter sentences that contain
            # target resources of entity's relationship
            for rel, resources in values.iteritems():
                wikipedia_target_resources = map(self.wikipedia_uri, resources)
                # DBP_target_resources = map(self.normalize_DBP_uri, resources)
                relevant_sentences = self.filter_relevant_sentences(html_text, wikipedia_target_resources)
                values[rel] = {'resources': wikipedia_target_resources,
                               'sentences': relevant_sentences}

    # ---------------------------------------------------------------------------------------------
    #                               Statistics and Visualizations
    # ---------------------------------------------------------------------------------------------

    def find_tokens_in_html(self, html, resource):
        soup = bs(html, 'lxml')
        reference = soup.find('a', {'href': resource})
        reference = reference.get_text()
        tokens = word_tokenize(reference)
        return tokens

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
        corpus = deepcopy(self.dbpedia)

        for entity, relations in corpus.iteritems():
            for rel_ontology, values in relations.iteritems():
                target_resources = values['resources']
                sentences = values['sentences']
                entity = self.normalize_uri(entity)
                rel_ontology = rel_ontology.split('/')[-1]
                data = [[entity, rel_ontology, res, sent]
                        for res in target_resources
                        for sent in sentences
                        if self.contains_any_reference(sent, [res]) and res != entity]
                # remove needless sentence information based on relation facts
                # data = map(self.shorten_sentence, data)
                # POS tag sentences
                for entry in data:
                    sentence = entry[3]
                    resource = entry[2]
                    soup = bs(sentence, 'lxml')
                    nl_sentence = soup.get_text()
                    entry.append(nl_sentence)
                    tokenized_sentences = map(word_tokenize, [nl_sentence])
                    pos_tagged_sentences = pos_tag_sents(tokenized_sentences).pop()
                    object_tokens = self.find_tokens_in_html(sentence, resource)
                    patterns = pattern_extractor.extract_patterns(nl_sentence, object_tokens)
                    entry.append(patterns[0])
                    entry.append(patterns[1])

                    # color sentence parts according to POS tag
                    colored_sentence = [colored(word, color_mapping.setdefault(pos, 'white'))
                                        for word, pos in pos_tagged_sentences]
                    colored_sentence = ' '.join(colored_sentence)
                    colored_sentence = re.sub(r' (.\[\d+m),', ',', colored_sentence)  # remove space before commas
                    entry.append(colored_sentence)

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
                          attrs={'concealed', 'bold'}) + colored(self.normalize_uri(entry[2]), 'white')).expandtabs(20)
            print(colored('[Wiki Occurence] \t',
                          'red', attrs={'concealed', 'bold'}) + entry[7]).expandtabs(20)
            print(colored('[Text Pattern] \t',
                          'red', attrs={'concealed', 'bold'}) + colored(entry[5], 'white')).expandtabs(20)
            print(colored('[Text Pattern] \t',
                          'red', attrs={'concealed', 'bold'}) + colored(entry[6], 'white')).expandtabs(20)
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

    def get_elapsed_time(self):
        return self.elapsed_time


if __name__ == '__main__':
    use_dump = True
    argv = sys.argv
    if len(argv) > 1:
        if argv[1] == '--dump':
            use_dump = True
        else:
            print 'Usage: python wiki_pattern.py [--dump]'

    wiki = WikiPatternExtractor(limit=30, use_dump=use_dump)
    # preprocess data
    wiki.discover_patterns()
    # print Part-of-speech tagged sentences
    wiki.print_patterns()
    # calculate occured facts coverage
    wiki.calculate_text_coverage()
