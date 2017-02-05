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


class TaggedSentence(object):
    def __init__(self, sentence, links, relative_position):
        self.sentence = []
        sentence = TaggedSentence.__clean_input(sentence)
        tokens = stanford_tokenizer.tokenize(sentence)
        for token in tokens:
            target_url = None
            for i in range(len(links)):
                link = links[i]
                if token == link[1]:
                    target_url = link[0]
                    links.pop(i)
                    break
            self.sentence.append(TaggedToken(token, target_url=target_url))

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
        return [tagged_s for paragraph in paragraphs
                for tagged_s in TaggedSentence.from_bs_tag(paragraph, sought_dbpedia_resources)]

    @classmethod
    def from_bs_tag(cls, bs_tag, sought_wiki_resources):
        # html = html.decode('utf-8')
        assert sought_wiki_resources == 'any' or len(sought_wiki_resources) > 0
        found_resources = []
        for link in bs_tag.find_all('a'):
            if sought_wiki_resources == 'any' or link.get('href') in sought_wiki_resources:
                found_resources.append((link.get('href'), link.get_text()))

        # get raw_text
        text = bs_tag.get_text()
        # split text by ". ", "! " or "? " and keep them in each item
        # https://stackoverflow.com/questions/14622835/split-string-on-or-keeping-the-punctuation-mark
        filtered_sentences = filter(lambda s: TaggedSentence.contains_a_link(s, found_resources),
                                    re.split('(?<=[.!?]) +', text))
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

    def is_link(self):
        return self._link is not None

    def __str__(self):
        string = self._text
        if self._link:
            string += ' (' + self._link + ')'
        return string
