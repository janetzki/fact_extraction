import imp
import requests
from timeit import default_timer as timer

tagged_sentence = imp.load_source('tagged_sentence', '../wikipedia_connector/tagged_sentence.py')
from tagged_sentence import TaggedSentence

dump_extractor = imp.load_source('dump_extractor', '../wikipedia_connector/wikipedia_dump_extractor.py')
from dump_extractor import WikipediaDumpExtractor

redirector = imp.load_source('subst_redirects', '../data_cleaning/redirects_substitutor.py')
uri_rewriting = imp.load_source('uri_rewriting', '../helper_functions/uri_rewriting.py')


class WikipediaConnector(object):
    def __init__(self, use_dump=False, redirect=False, redirects_path='../data/redirects_en.txt'):
        self.elapsed_time = 0  # for performance monitoring

        if use_dump:
            self.wikipedia_dump_extractor = WikipediaDumpExtractor()
        else:
            self.wikipedia_dump_extractor = None

        if redirect and not use_dump:
            self.redirector = redirector.RedirectsSubstitutor(redirects_path)
        else:
            self.redirector = False

    def get_wikipedia_article_html(self, dbpedia_resource):
        start = timer()
        if self.wikipedia_dump_extractor is not None:
            resource = uri_rewriting.strip_cleaned_name(dbpedia_resource)
            html = self.wikipedia_dump_extractor.get_wikipedia_html_from_dump(resource)
        else:
            html = self._scrape_wikipedia_article(dbpedia_resource)
        end = timer()
        self.elapsed_time += end - start
        return html

    def _scrape_wikipedia_article(self, dbpedia_resource):
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

    @staticmethod
    def _make_html_to_tagged_sentences(html, wikipedia_resources):
        return [tagged_s for tagged_s in TaggedSentence.from_html(html, wikipedia_resources)]

    def get_filtered_wikipedia_article(self, dbpedia_resource, sought_wiki_resources='any'):
        html = self.get_wikipedia_article_html(dbpedia_resource)
        return WikipediaConnector._make_html_to_tagged_sentences(html, sought_wiki_resources)


def test(wikipedia_connector, resource):
    wikipedia_connector.get_filtered_wikipedia_article(resource)


if __name__ == '__main__':
    wikipedia_connector = WikipediaConnector(use_dump=True)
    test(wikipedia_connector, 'Alexander_I_of_Serbia')
    test(wikipedia_connector, 'Andrew Wiles')
