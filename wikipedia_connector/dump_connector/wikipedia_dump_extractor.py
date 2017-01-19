import re
import csv
import imp
from bs4 import BeautifulSoup as bs
from tqdm import tqdm

line_counting = imp.load_source('line_counting', '../helper_functions/line_counting.py')


class WikipediaDumpExtractor(object):
    def __init__(self, dump_path='../data/enwiki-latest-pages-articles-redirected.xml',
                 index_path='../data/character_index_sorted.csv'):
        self.dump_path = dump_path
        self.character_index = {}
        self.delimiter = '#'
        self._load_character_index(index_path)

    def _load_character_index(self, types_path):
        total_lines = line_counting.count_lines(types_path)
        print('\n\nReading character index file...')
        with open(types_path, 'r') as fin:
            reader = csv.reader(fin, delimiter=self.delimiter)
            for subject, character_offset in tqdm(reader, total=total_lines):
                self.character_index[subject] = int(character_offset)

    def _extract_wikipedia_page_via_offset(self, offset):
        with open(self.dump_path, 'r') as fin:
            fin.seek(offset)
            page = ''
            for line in fin:
                if len(page) == 0:
                    assert line == '  <page>\n'  # otherwise the character index does not match the dump
                page += line
                if line[0:9] == '  </page>':
                    break
            return page

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
        offset = self.character_index.setdefault(resource, None)
        if offset is None:
            return ''  # no article found, resource probably contains non-ASCII character TODO: Heed this case.
        page = self._extract_wikipedia_page_via_offset(offset)
        text = WikipediaDumpExtractor._extract_wikipedia_text_from_page(page)
        html_text = WikipediaDumpExtractor._make_wikipedia_text_to_html(text)
        return html_text
