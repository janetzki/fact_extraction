#!../venv/bin/python
# -*- coding: utf-8 -*-

from __future__ import division
from bs4 import BeautifulSoup as bs
from nltk.tokenize import sent_tokenize, word_tokenize
import re

import sys

reload(sys)
sys.setdefaultencoding('utf-8')


class TaggedSentence(object):
    def __init__(self, sentence, relative_position):
        self.sentence = []

        for word in self._yield_words(self.__cleanInput(sentence)):
            if word.strip(',').startswith('#') and word.strip(',').endswith('#'):
                link, text = word.split('#')[1], word.split('#')[2]
                self.sentence.append(TaggedToken(text, target_url=link))
                continue
            self.sentence.append(TaggedToken(word))

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

    def _yield_words(self, sentence):
        # yield seperate word orfull meta tagged links
        link_component = None
        for word in sentence.split(' '):
            if word.strip(',').startswith('#') and not word.strip(',').endswith('#'):
                link_component = word
                continue
            if link_component:
                if word.endswith('#'):
                    word = link_component + ' ' + word
                    link_component = None
                else:
                    link_component += word
                    continue
            yield word

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

    def contains_any(self, resources):
        resources = map(lambda s: s.replace("/wiki/", ''), resources)
        contained_links = map(lambda token: token.link.replace('/wiki/', ''), self.links)
        for res in resources:
            if res in contained_links:
                return True
        return False

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

    @classmethod
    def parse_html(cls, bs_tag):
        # replace links with intermediary representation
        # html = html.decode('utf-8')
        for link in bs_tag.find_all('a'):
            target = link.get('href')
            if target.startswith('#') or not link.string:
                continue  # ignore intern links and links with no enclosed text
            link.string = '#' + target + '#' + link.string + '#'

        # get raw_text
        text = bs_tag.get_text()
        # split sentences
        sentences = sent_tokenize(text)
        count = sentences.__len__()
        return [TaggedSentence(sent, i / count) for i, sent in enumerate(sentences)]


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
