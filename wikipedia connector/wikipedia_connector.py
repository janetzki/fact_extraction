import imp
import requests
from timeit import default_timer as timer
from bs4 import BeautifulSoup as bs

dump_extractor = imp.load_source('dump_extractor', '../wikipedia connector/dump connector/dump_extractor.py')


class WikipediaConnector(object):
    def __init__(self, use_dump=False):
        self.use_dump = use_dump
        self.elapsed_time = 0  # for performance monitoring

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