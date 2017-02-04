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
        total_lines = line_counting.cached_counter.count_lines(types_path)
        print('\n\nReading character index file...')
        with open(types_path, 'rb') as fin:
            reader = csv.reader(fin, delimiter=self.delimiter)
            for subject, character_offset in tqdm(reader, total=total_lines):
                self.character_index[subject] = int(character_offset)

    def _extract_wikipedia_page_via_offset(self, offset):
        with open(self.dump_path, 'rb') as fin:
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

        # truncate article
        html_text = re.sub(r'==Further reading==(.|\n)*', '', html_text)

        # remove all headlines
        html_text = re.sub(r'[\n](=+).*?(\1)[\n]', '', html_text)
        html_text = re.sub(r"'''.*?'''", '', html_text)

        # insert paragraphs
        html_text = re.sub(r'(.+\n)', r'<p>\1</p>', html_text)

        # drop reference tags
        html_text = re.sub(r'<ref( .*?)?/>', '', html_text)
        html_text = re.sub(r'<ref( .*?)?>(.|\n)*?</ref>', '', html_text)

        # drop possibly nested file and image links
        no_bracket = r'[^\[\]]'
        no_brackets = no_bracket + r'*'
        single_brackets = r'(\[' + no_brackets + r'\])'
        double_brackets = r'(\[\[' + no_brackets + r'\]\])'
        single_or_double_brackets = r'((' + single_brackets + r'|' + double_brackets + r')' + no_brackets + r')'
        embedded_brackets = no_brackets + single_or_double_brackets + r'*' + no_brackets
        html_text = re.sub(r'\[\[((File)|(Image)):' + embedded_brackets + r'\]\]', '', html_text)

        # drop possibly nested external links
        html_text = re.sub(r'\[https?://' + no_bracket + embedded_brackets + '\]', '', html_text)

        html_text = re.sub(r'\[\[Category:' + no_brackets + r'\]\]', '', html_text)
        html_text = re.sub(r'\* ?', '', html_text)

        # insert HTML links
        rx_references = re.compile(r'\[\[([^\|\]]*)\|?(.*?)\]\]')
        html_text = re.sub(rx_references, WikipediaDumpExtractor._replace_links, html_text)

        # occurences of this are strange, e.g., [Obama's] --> Obama's in article of Angela Merkel
        html_text = re.sub(r'\[(.*?)\]', r'\1', html_text)
        return html_text

    @staticmethod
    def _is_wikimarkup_consistent(text):
        if text.count('[') != text.count(']'):
            return False
        if text.count('{') != text.count('}'):
            return False
        return True

    @staticmethod
    def _test_cleaning(html):
        bad_strings = ['==', '{', '}', '[', ']', '<ref']
        for string in bad_strings:
            if html.find(string) >= 0:
                print('[WARN]   HTML is not clean. Found: "' + string + '"')

    def get_wikipedia_html_from_dump(self, resource):
        corrupted_articles = ['Doctor Who', 'Amsterdam']
        if resource in corrupted_articles:
            print('[WARN]   Resource is listed as corrupted.')
            return ''
        offset = self.character_index.setdefault(resource, None)
        # assert offset is not None
        if offset is None:
            print('[WARN]   Resource not found in character index.')
            return ''  # probably because of Issue #64 (https://github.com/jjanetzki/fact_extraction/issues/64)
        page = self._extract_wikipedia_page_via_offset(offset)
        text = WikipediaDumpExtractor._extract_wikipedia_text_from_page(page)
        if not WikipediaDumpExtractor._is_wikimarkup_consistent(text):
            pass
        html_text = WikipediaDumpExtractor._make_wikipedia_text_to_html(text)
        WikipediaDumpExtractor._test_cleaning(html_text)
        return html_text

    @staticmethod
    def test_html_conversion():
        input = '[[File:ThreeMenWalkingII.JPG|thumb|''Three Men Walking II'', 1949, painted bronze sculpture [[Metropolitan Museum of Art]]. "The surfaces of Three Men Walking (II), 1949, typify his technique."<ref name="Metropolitan Museum of Art">[http://www.metmuseum.org/Collections/search-the-collections/489978?rpp=20&pg=1&ao=on&ft=alberto+giacometti&pos=6 Metropolitan Museum of Art]</ref>]]'
        assert WikipediaDumpExtractor._is_wikimarkup_consistent(input)
        output = WikipediaDumpExtractor._make_wikipedia_text_to_html(input)
        assert output == ''


if __name__ == '__main__':
    WikipediaDumpExtractor.test_html_conversion()
