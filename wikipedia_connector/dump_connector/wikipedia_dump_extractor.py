import re
import csv
from bs4 import BeautifulSoup as bs


class WikipediaDumpExtractor(object):
    def __init__(self, dump_path='../data/enwiki-latest-pages-articles-redirected.xml',
                 index_path='../data/index-r.csv'):
        self.dump_path = dump_path
        self.index_path = index_path

    def _get_dump_offset_via_index(self, title):
        with open(self.index_path, 'r') as fin:
            indexreader = csv.reader(fin, delimiter='#')
            for line in indexreader:
                if line[0] == title:
                    fin.close()
                    return int(line[1])
            fin.close()
        return None

    def _extract_wikipedia_page_via_offset(self, offset):
        with open(self.dump_path, 'r') as fin:
            fin.seek(offset)
            text = "  <page>\n"
            for line in fin:
                text += line
                if line[0:9] == "  </page>":
                    break
            return text

    @staticmethod
    def _extract_wikipedia_text_from_page(page):
        soup = bs(page, 'lxml')
        return soup.find('text').get_text()

    @staticmethod
    def _strip_outer_brackets(text):
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

    @staticmethod
    def _replace_links(match):
        resource, text = match.groups()
        if text == "":
            text = resource
        resource = resource.replace(' ', '_')
        html_link = '<a href="/wiki/' + resource + '">' + text + '</a>'
        return html_link

    @staticmethod
    def _make_wikipedia_text_to_html(text):
        """ No perfect HTML - just for unified processing, e.g., link search """
        # drop infobox and other garbage inside {...}
        html_text = WikipediaDumpExtractor._strip_outer_brackets(text)

        # remove all headlines
        html_text = re.sub(r'(=+).*?(\1)', '', html_text)
        html_text = re.sub(r"'''.*?'''", '', html_text)

        html_text = re.sub(r'\[\[Category:.*\]\]', '', html_text)
        html_text = re.sub(r'\[http://.*?\]', '', html_text)  # drop hyperlinks
        html_text = re.sub(r'\* ?', '', html_text)

        # insert HTML links
        rx_references = re.compile(r'\[\[([^\|\]]*)\|?(.*?)\]\]')
        html_text = re.sub(rx_references, WikipediaDumpExtractor._replace_links, html_text)
        return html_text

    def get_wikipedia_html_from_dump(self, resource):
        offset = self._get_dump_offset_via_index(resource)
        if offset is None:
            return ''  # no article found, resource probably contains non-ASCII character TODO: Heed this case.
        page = self._extract_wikipedia_page_via_offset(offset)
        text = WikipediaDumpExtractor._extract_wikipedia_text_from_page(page)
        html_text = WikipediaDumpExtractor._make_wikipedia_text_to_html(text)
        return html_text
