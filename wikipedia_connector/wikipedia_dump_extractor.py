from logger import Logger
from helper_functions import line_counting
from tqdm import tqdm
from lxml import html
import re
import unicodecsv
import os
import io

dir_path = os.path.dirname(os.path.abspath(__file__)) + '/'


class WikipediaDumpExtractor(object):
    def __init__(self, dump_path=dir_path + '../data/enwiki-latest-pages-articles-redirected.xml',
                 index_path=dir_path + '../data/character_index_sorted.csv'):  # sorted index does not contain all testing resources
        self.dump_path = dump_path
        self.character_index = {}
        self.delimiter = '#'
        self.logger = Logger.from_config_file()
        self._load_character_index(index_path)

    def _load_character_index(self, character_index_path):
        total_lines = line_counting.cached_counter.count_lines(character_index_path)
        self.logger.print_info('Reading character index file...')
        with io.open(character_index_path, 'r', encoding='utf8') as fin:
            reader = unicodecsv.reader(fin, delimiter=self.delimiter)
            for subject, character_offset in tqdm(reader, total=total_lines):
                self.character_index[subject] = int(character_offset)

    def _extract_wikipedia_page_via_offset(self, offset):
        with open(self.dump_path, 'rb') as fin:
            fin.seek(offset)
            page = ''
            for line in fin:
                if len(page) == 0:
                    assert line[:8] == '  <page>'  # otherwise the character index does not match the dump
                page += line
                if line[0:9] == '  </page>':
                    break
            return page

    @staticmethod
    def _extract_wikipedia_text_from_page(page):
        # soup = bs(page, 'lxml')
        # return soup.find('text').get_text()
        document = html.fromstring(page)
        return document.findtext('.//text')

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

        # remove comments
        html_text = re.sub(r'<!--(.|\n)*?-->', '', html_text)

        # truncate article
        html_text = re.sub(r'== *Further reading *==(.|\n)*', '', html_text)
        html_text = re.sub(r'== *References *==(.|\n)*', '', html_text)

        # remove all headlines
        html_text = re.sub(r'^(=+).+?(\1)', '\n', html_text, flags=re.MULTILINE)

        # drop reference tags
        html_text = re.sub(r'<(r|R)ef(( |\n)[^>]*?)?\/>', '', html_text)
        html_text = re.sub(r'<(r|R)ef(( |\n)[^>]*?[^\/])?>(.|\n)*?<\/(r|R)ef>', '', html_text)

        # drop possibly nested file and image links
        no_bracket = r'[^\[\]]'
        no_brackets = no_bracket + r'*'
        single_brackets = r'(\[' + no_brackets + r'\])'
        double_brackets = r'(\[\[' + no_brackets + r'\]\])'
        single_or_double_brackets = r'((' + single_brackets + r'|' + double_brackets + r')' + no_brackets + r')'
        embedded_brackets = no_brackets + single_or_double_brackets + r'*' + no_brackets
        html_text = re.sub(r'\[\[((File)|(Image)):' + embedded_brackets + r'\]\]', '', html_text)

        # drop possibly nested external links
        html_text = re.sub(r'\[https?:\/\/' + no_bracket + embedded_brackets + '\]', '', html_text)

        html_text = re.sub(r'\[\[Category:' + no_brackets + r'\]\]', '', html_text)
        html_text = re.sub(r'\* ?', '', html_text)

        # remove bold face and italics
        html_text = re.sub(r"'{2,3}", '', html_text)

        # insert paragraphs (at least two linebreaks required)
        html_text = re.sub(r'((.(.|\n)+?)\n\n)', r'<p>\2</p>', html_text)

        # insert HTML links
        rx_references = re.compile(r'\[\[([^\|\]]*)\|?(.*?)\]\]')
        html_text = re.sub(rx_references, WikipediaDumpExtractor._replace_links, html_text)

        # occurrences of this are strange, e.g., [Obama's] --> Obama's in article of Angela Merkel
        html_text = re.sub(r'\[(.*?)\]', r'\1', html_text)

        # remove empty paragraphs
        html_text = re.sub(r'<p>[ \n]*<\/p>', '', html_text)

        # make paragraphs equidistant
        html_text = re.sub(r'<\/p>\n*<p>', '</p>\n\n<p>', html_text)
        return html_text

    @staticmethod
    def _is_wikimarkup_consistent(text):
        if text.count('[') != text.count(']'):
            return False
        if text.count('{') != text.count('}'):
            return False
        return True

    def _test_cleaning(self, html):
        bad_strings = ['==', '{', '}', '[', ']', '<ref>', '<ref ', '</ref>', '\r', '<!--', '-->', "''"]
        for string in bad_strings:
            if html.find(string) >= 0:
                self.logger.print_warning('HTML is not clean. Found: "' + string + '"')

    def get_wikipedia_html_from_dump(self, resource):
        offset = self.character_index.setdefault(resource, None)
        if offset is None:
            self.logger.print_error('Resource not found in character index: "' + resource + '"')
            return ''
        page = self._extract_wikipedia_page_via_offset(offset)
        text = WikipediaDumpExtractor._extract_wikipedia_text_from_page(page)
        if not WikipediaDumpExtractor._is_wikimarkup_consistent(text):
            self.logger.print_warning('Wikimarkup might be inconsistent.')
        html_text = WikipediaDumpExtractor._make_wikipedia_text_to_html(text)
        self._test_cleaning(html_text)
        return html_text

    @staticmethod
    def test_html_conversion():
        input = '[[File:ThreeMenWalkingII.JPG|thumb|''Three Men Walking II'', 1949, painted bronze sculpture [[Metropolitan Museum of Art]]. "The surfaces of Three Men Walking (II), 1949, typify his technique."<ref name="Metropolitan Museum of Art">[http://www.metmuseum.org/Collections/search-the-collections/489978?rpp=20&pg=1&ao=on&ft=alberto+giacometti&pos=6 Metropolitan Museum of Art]</ref>]]'
        assert WikipediaDumpExtractor._is_wikimarkup_consistent(input)
        output = WikipediaDumpExtractor._make_wikipedia_text_to_html(input)
        assert output == ''


if __name__ == '__main__':
    WikipediaDumpExtractor.test_html_conversion()
