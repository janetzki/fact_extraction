import imp
import requests
import re
from timeit import default_timer as timer
from bs4 import BeautifulSoup as bs
from nltk.tokenize import sent_tokenize, word_tokenize

dump_extractor = imp.load_source('dump_extractor', '../wikipedia_connector/dump_connector/dump_extractor.py')
redirector = imp.load_source('subst_redirects', '../data_cleaning/subst_redirects.py')
tagged_sentence = imp.load_source('tagged_sentence', '../wikipedia_connector/tagged_sentence.py')

from tagged_sentence import TaggedSentence


class WikipediaConnector(object):
    def __init__(self, use_dump=False, redirect=False, redirects_path='../data/redirects_en.txt'):
        self.use_dump = use_dump
        self.elapsed_time = 0  # for performance monitoring
        if redirect and not use_dump:
            self.redirector = redirector.Substitutor(redirects_path)
        else:
            self.redirector = False

    def _get_wikipedia_article(self, dbpedia_resource):
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

    def scrape_wikipedia_article(self, dbpedia_resource):
        """
        Requests wikipedia resource per GET request - extracts text content
        and returns text
        """
        # http://dbpedia.org/resource/Alain_Connes -> http://en.wikipedia.org/wiki/Alain_Connes
        wiki_url = dbpedia_resource.replace("dbpedia.org/resource", "en.wikipedia.org/wiki")

        response = requests.get(wiki_url)
        article = response.content.decode('utf-8')
        if self.redirector:
            article = self.redirector.substitute_html(article)
        return article

    def normalize_uri(self, uri):
        """
        http://dbpedia.org/resource/Alain_Connes -> 'Alain Connes'
        """
        name = uri.split('/')[-1].replace('_', ' ')
        return TaggedSentence.clean_input(name)

    def wikipedia_uri(self, DBP_uri):
        return DBP_uri.replace("http://dbpedia.org/resource/", "/wiki/")

    def splitkeepsep(self, s, sep):
        """ http://programmaticallyspeaking.com/split-on-separator-but-keep-the-separator-in-python.html """
        return reduce(lambda acc, elem: acc[:-1] + [acc[-1] + elem] if elem == sep else acc + [elem],
                      re.split("(%s)" % re.escape(sep), s), [])

    @staticmethod
    def has_appropriate_text_length(html):
        soup = bs(html, 'lxml')
        length = len(soup.get_text())
        return 0 < length < 200

    def clean_tags(self, html_text):
        # html_text = re.sub(r'<[^a].*?>', '', html_text) # Intention: Only keep <a></a> Tags. Problem: Deletes </a> tags.
        html_text = '<p>' + html_text + '</p>'
        return html_text

    def find_tokens_in_html(self, html, resource):
        soup = bs(html, 'lxml')
        reference = soup.find('a', {'href': resource})
        reference_text = reference.get_text()
        return word_tokenize(reference_text)

    def find_tokens_in_sentence(self, sentence, resource):
        links = sentence.links
        for link in links:
            if link.link == resource:
                tokens = word_tokenize(link.text)
                return tokens

    def _make_to_tagged_sentences(self, html):
        return [tagged_s for paragraph in html for tagged_s in TaggedSentence.parse_html(paragraph)]

    def get_parsed_wikipedia_article(self, dbpedia_resource):
        html = self._get_wikipedia_article(dbpedia_resource)
        return self._make_to_tagged_sentences(html)
