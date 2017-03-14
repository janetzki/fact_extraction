from __future__ import division
from bs4 import BeautifulSoup as bs
from nltk.tokenize import StanfordTokenizer
import re
import sys
import imp


uri_rewriting = imp.load_source('uri_rewriting', '../helper_functions/uri_rewriting.py')

reload(sys)
sys.setdefaultencoding('utf-8')

stanford_tokenizer = StanfordTokenizer(path_to_jar='../stanford-corenlp-full-2016-10-31/stanford-corenlp-3.7.0.jar')


class TokenMatcher(object):
    """
    NFA that matches a sequence of tokens
    Each current_match is a state.
    """

    def __init__(self, pattern_tokens):
        self.pattern_tokens = pattern_tokens
        self.current_matches = {-1}

    def match_next_token(self, token):
        new_matches = {-1}
        for current_match in self.current_matches:
            if current_match == len(self.pattern_tokens) - 1:
                continue
            match = token == self.pattern_tokens[current_match + 1]
            if match:
                new_matches.add(current_match + 1)
        self.current_matches = new_matches

    def complete_match(self):
        return len(self.pattern_tokens) - 1 in self.current_matches

    def match_indices(self, tokens):
        match_indices = []
        for i in range(len(tokens)):
            self.match_next_token(tokens[i])
            if self.complete_match():
                match_indices.append(i)
        return match_indices

    def full_match_indices(self, tokens):
        match_indices = set()
        for index in self.match_indices(tokens):
            for i in range(len(self.pattern_tokens)):
                match_indices.add(index - i)
        return match_indices

    def count_matches(self, tokens):
        return len(self.match_indices(tokens))

    @staticmethod
    def test_matching():
        assert TokenMatcher(['1', '0', '1', '0']).count_matches(['1', '0', '1', '1', '0', '1', '0']) == 1
        assert TokenMatcher(['1', '0', '1', '0']).count_matches(['1', '0', '1', '0', '1', '0']) == 2
        assert TokenMatcher(['0', '1', '0', '0']).count_matches(['0', '1', '0', '1', '0', '0']) == 1
        assert TokenMatcher(['Baltimore', ',', 'Maryland']).full_match_indices(
            ['Born', 'Elinor', 'Isabel', 'Judefind', 'in', 'Baltimore', ',', 'Maryland']) == {5, 6, 7}


class TaggedSentence(object):
    """
    Data structure that is containing a tokenized sentenced. In case a word is hyperlinked,
    the linked entity is stored as well.
    """
    def __init__(self, sentence, links, relative_position):
        self.sentence = []
        sentence = TaggedSentence.__clean_input(sentence)
        tokens = stanford_tokenizer.tokenize(sentence)

        links = [(link[0], TokenMatcher(stanford_tokenizer.tokenize(link[1]))) for link in links]
        for token in tokens:
            self.sentence.append(TaggedToken(token))
        for link in links:
            for index in link[1].full_match_indices(tokens):
                self.sentence[index].set_link(link[0])

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

    # @property
    # def link_positions(self):
    #     return [(token, position) for token in enumerate(self.sentence) if token.is_link()]

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
    def from_html(cls, html, sought_dbpedia_resources='any'):
        soup = bs(html, 'lxml')
        paragraphs = TaggedSentence.extract_paragraphs(soup)
        return [tagged_s for i, paragraph in enumerate(paragraphs)
                for tagged_s in TaggedSentence.from_bs_tag(paragraph, sought_dbpedia_resources, i / len(paragraphs))]

    @classmethod
    def from_bs_tag(cls, bs_tag, sought_wiki_resources, relative_position):
        # html = html.decode('utf-8')
        assert sought_wiki_resources == 'any' or len(sought_wiki_resources) > 0
        found_resources = []
        for link in bs_tag.find_all('a'):
            if sought_wiki_resources == 'any' or link.get('href') in sought_wiki_resources:
                found_resources.append((link.get('href'), link.get_text()))

        # get raw_text
        text = bs_tag.get_text()
        lines = text.split('\n')
        # split text by ". ", "! " or "? " and keep them in each item
        # https://stackoverflow.com/questions/14622835/split-string-on-or-keeping-the-punctuation-mark
        sentences = [sentence for line in lines for sentence in re.split('(?<=[.!?]) +', line)]
        filtered_sentences = filter(lambda s: TaggedSentence.contains_a_link(s, found_resources), sentences)
        tagged_sentences = [TaggedSentence(sent, found_resources, relative_position) for sent in filtered_sentences]
        return tagged_sentences

    def contained_links(self):
        links = set()
        for token in self.tokens:
            if token.is_link():
                links.add(token.link)
        return links

    @staticmethod
    def contains_a_link(sentence, links):
        links_words = [words for link, words in links]
        for link_words in links_words:
            if link_words in sentence:
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

    def addresses_of_dbpedia_links(self):
        addresses_of_links = self.addresses_of_links()
        for link in addresses_of_links.keys():
            dbpedia_link = uri_rewriting.convert_to_dbpedia_resource_uri(link)
            addresses_of_links[dbpedia_link] = addresses_of_links.pop(link)
        return addresses_of_links

    def addresses_of_link(self, link):
        assert isinstance(link, unicode)
        addresses_of_all_contained_links = self.addresses_of_links()
        if link not in addresses_of_all_contained_links:
            # just for debugging
            print('Link: ' + str(link))
            print('All links: ' + str(addresses_of_all_contained_links))
        return addresses_of_all_contained_links[link]

    @staticmethod
    def __clean_input(string):
        """
        Sanitize text - remove multiple new lines and spaces - get rid off non ascii chars -
        strip words from punctuation signs - returns sanitized string
        """
        string = re.sub('\n+', " ", string)
        string = re.sub(' +', " ", string)

        # get rid off non-ascii characters
        string = re.sub(r'[^\x00-\x7f]', r'', string)

        string = re.sub(r'\[\d+\]', r'', string)
        clean_input = []
        string = string.split(' ')
        for item in string:
            # item = item.strip('?!;,')
            if len(item) > 1 or (item.lower() == 'a' or item == 'I'):
                clean_input.append(item)
        return ' '.join(clean_input).encode('utf-8')


class TaggedToken(object):
    """
    Represents a word in a sentence. Furthermore it can be hyperlinked to an entity
    """
    def __init__(self, token, target_url=None):
        super(TaggedToken, self).__init__()
        self._text = token
        self._link = target_url
        # TODO if target url is set look for dbpedia redirects as aliases
        if target_url is not None and len(target_url) > 0:
            self._link = uri_rewriting.capitalize(target_url)  # Hotfix for issue #72, TODO: find better solution

    @property
    def text(self):
        return self._text

    @property
    def link(self):
        return self._link

    def set_link(self, link):
        self._link = link

    def is_link(self):
        return self._link is not None

    def __str__(self):
        string = self._text
        if self._link:
            string += ' (' + self._link + ')'
        return string


def test_html_parsing():
    TaggedSentence.from_html(
        'Born Elinor Isabel Judefind in <a href="/wiki/Baltimore" class="mw-redirect" title="Baltimore, Maryland">Baltimore, Maryland</a> , to parents of French-German descent , Agnew was daughter of William Lee Judefind , a <a href="/wiki/Chemist">chemist</a> , and his wife , the former Ruth Elinor Schafer . ')


if __name__ == '__main__':
    TokenMatcher.test_matching()
    test_html_parsing()
