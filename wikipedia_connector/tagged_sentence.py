#!../venv/bin/python
# -*- coding: utf-8 -*-

from __future__ import division
from bs4 import BeautifulSoup as bs
from nltk.tokenize import sent_tokenize
import sys
import imp

reload(sys)
sys.setdefaultencoding('utf-8')

uri_rewriting = imp.load_source('uri_rewriting', '../helper_functions/uri_rewriting.py')


class TaggedSentence(object):
    def __init__(self, sentence, relative_position):
        self.sentence = []

        for word in self._yield_words(uri_rewriting.clean_input(sentence)):
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

    def number_of_tokens(self):
        return len(self.sentence)

    def _yield_words(self, sentence):
        # yield seperate word or full meta tagged links
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
    def from_html(cls, html):
        soup = bs(html, 'lxml')
        paragraphs = TaggedSentence.extract_paragraphs(soup)
        return [tagged_s for paragraph in paragraphs for tagged_s in TaggedSentence.from_bs_tag(paragraph)]

    @classmethod
    def from_bs_tag(cls, bs_tag):
        # replace links with intermediary representation
        # html = html.decode('utf-8')
        for link in bs_tag.find_all('a'):
            target = link.get('href')
            if target is None:
                pass
            assert target is not None
            if target.startswith('#') or not link.string:  # cite_notes start with '#'
                continue  # ignore intern links and links with no enclosed text
            link.string = '#' + target + '#' + link.string + '# '  # space at end ensures that punctuation marks after word won't be considered as part of it

        # get raw_text
        text = bs_tag.get_text()
        # split sentences
        sentences = sent_tokenize(text)
        count = sentences.__len__()
        return [TaggedSentence(sent, i / count) for i, sent in enumerate(sentences)]

    def contained_links(self):
        links = set()
        for token in self.tokens:
            if token.is_link():
                links.add(token.link)
        return links

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
