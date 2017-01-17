#!../venv/bin/python
# -*- coding: utf-8 -*-

from __future__ import division
from bs4 import BeautifulSoup as bs
from nltk.tokenize import StanfordTokenizer
import os
path_to_jar = os.path.join('..', 'stanford-corenlp-full-2016-10-31', 'stanford-corenlp-3.7.0.jar')
import re
import sys
import imp

reload(sys)
sys.setdefaultencoding('utf-8')
tokenizer = StanfordTokenizer(path_to_jar=path_to_jar)


uri_rewriting = imp.load_source('uri_rewriting', '../helper_functions/uri_rewriting.py')


class TaggedSentence(object):
    def __init__(self, sentence, links, relative_position):
        self.sentence = []
        sentence = self.__cleanInput(sentence)
        link_words = map(lambda x: x[1], links)
        tokens = tokenizer.tokenize(sentence)
        tagged = []
        for token in tokens:
            if token in link_words:
                for link in links:
                    if token in link[1]:
                        self.sentence.append(TaggedToken(token, target_url=link[0]))
            else:
                self.sentence.append(TaggedToken(token))


        # self.sentence = sentence  # provisional - TODO: replace with token and tag list
        self.relative_position = relative_position  # zero based counting

    def __str__(self):
        sent = ''
        for token in self.sentence:
            sent += (token.text + ' ')
        return sent

    @property
    def tokens(self):
        return self.sentence

    def number_of_tokens(self):
        return len(self.sentence)

    def as_string(self):
        return self.__str__()

    @property
    def link_positions(self):
        return [(token, position) for token in enumerate(self.sentence) if token.is_link()]

    @property
    def links(self):
        return [token for token in self.sentence if token.is_link()]

    @property
    def relative_pos(self):
        return self.relative_position

    def contains_any_link(self, resources=None):
        if resources is None:
            if len(self.links) > 0:
                return True
            else:
                return False

        resources = map(lambda s: s.replace("/wiki/", ''), resources)
        contained_links = map(lambda token: token.link.replace('/wiki/', ''), self.links)
        for res in resources:
            if res in contained_links:
                return True
        return False

    @staticmethod
    def extract_paragraphs(soup):
        return soup.find_all('p')

    @classmethod
    def from_html(cls, html, sought_dbpedia_resources):
        soup = bs(html, 'lxml')
        paragraphs = TaggedSentence.extract_paragraphs(soup)
        return [tagged_s for paragraph in paragraphs
                         for tagged_s in TaggedSentence.from_bs_tag(paragraph, sought_dbpedia_resources)]

    @classmethod
    def from_bs_tag(cls, bs_tag, sought_wiki_resources):
        # html = html.decode('utf-8')
        found_resources = []
        for link in bs_tag.find_all('a'):
            if link.get('href') in sought_wiki_resources:
                found_resources.append((link.get('href'), link.get_text()))

        # get raw_text
        text = bs_tag.get_text()
        # split text by ". ", "! " or "? " and keep them in each item
        # https://stackoverflow.com/questions/14622835/split-string-on-or-keeping-the-punctuation-mark
        filtered_sentences = filter(lambda s: TaggedSentence.contains_a_link(s, found_resources),
                                    re.split('(?<=[.!?]) +',text))
        if not filtered_sentences:
            return []
        # split sentences
        count = filtered_sentences.__len__()
        return [TaggedSentence(sent, found_resources, i / count) for i, sent in enumerate(filtered_sentences)]

    def contained_links(self):
        links = set()
        for token in self.tokens:
            if token.is_link():
                links.add(token.link)
        return links

    @staticmethod
    def contains_a_link(sentence, links):
        link_words = [words for words in map(lambda l: l[1], links)]
        for link in link_words:
            if link in sentence:
                return True
        return False

    def addresses_of_links(self):
        links = self.contained_links()
        addresses_of_links = {link: [] for link in links}
        for i in range(len(self.sentence)):
            token = self.sentence[i]
            if token.link in links:
                addresses_of_links[token.link].append(i)
        return addresses_of_links

    def addresses_of_link(self, link):
        addresses_of_all_contained_links = self.addresses_of_links()
        assert link in addresses_of_all_contained_links
        return addresses_of_all_contained_links[link]

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
        return ' '.join(cleanInput).encode('utf-8')

class TaggedToken(object):
    def __init__(self, token, target_url=None):
        super(TaggedToken, self).__init__()
        self._text = token
        self._link = target_url
        # TODO if target url is set look for dbpedia redirects as aliases

    @property
    def text(self):
        return self._text

    @property
    def link(self):
        return self._link

    def is_link(self):
        if self._link:
            return True
        else:
            return False

    def __str__(self):
        string = self._text
        if self._link:
            string += ' (' + self._link + ')'
        return string
