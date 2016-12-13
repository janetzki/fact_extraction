import imp
import requests
import re
from timeit import default_timer as timer
from bs4 import BeautifulSoup as bs
from nltk.tokenize import sent_tokenize, word_tokenize

dump_extractor = imp.load_source('dump_extractor', '../wikipedia_connector/dump_connector/dump_extractor.py')
tagged_sentence = imp.load_source('tagged_sentence', '../pattern_learning/tagged_sentence.py')
redirector = imp.load_source('subst_redirects', '../data_cleaning/subst_redirects.py')
from tagged_sentence import TaggedSentence


class WikipediaConnector(object):
    def __init__(self, use_dump=False, redirects_path='../data/redirects_en.txt'):
        self.use_dump = use_dump
        self.elapsed_time = 0  # for performance monitoring
        if use_dump:
            self.redirector = redirector.Substitutor(redirects_path)
        else:
            self.redirector = False

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

    def clean_tags(self, html_text):
        # html_text = re.sub(r'<[^a].*?>', '', html_text) # Intention: Only keep <a></a> Tags. Problem: Deletes </a> tags.
        html_text = '<p>' + html_text + '</p>'
        return html_text

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
