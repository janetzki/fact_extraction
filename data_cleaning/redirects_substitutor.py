from tqdm import tqdm
import re
import csv
import imp
import sys

line_counting = imp.load_source('line_counting', '../helper_functions/line_counting.py')

reload(sys)
sys.setdefaultencoding('utf-8')


# def unicode_csv_reader(utf8_data, dialect=csv.excel, **kwargs):
#     csv_reader = csv.reader(utf8_data, dialect=dialect, **kwargs)
#     for row in csv_reader:
#         yield [unicode(cell, 'utf-8') for cell in row]


class RedirectsSubstitutor:
    def __init__(self, path_dump='../data/enwiki-latest-pages-articles.xml',
                 path_substituted_dump='../data/enwiki-latest-pages-articles-redirected.xml',
                 path_redirects='../data/redirects_en.csv'):
        self.path_dump = path_dump
        self.path_substituted_dump = path_substituted_dump
        self.redirects = {}
        self.delimiter = '#'
        self._load_redirects(path_redirects)

    def _load_redirects(self, redirects_path):
        total_lines = line_counting.cached_counter.count_lines(redirects_path)
        tqdm.write('\n\nReading redirects file...')
        with open(redirects_path, 'rb') as fin:
            reader = csv.reader(fin, delimiter=self.delimiter)
            for name, resource in tqdm(reader, total=total_lines):
                self.redirects[name] = resource

    def _substitute(self, resource, false_if_none=False):
        if resource in self.redirects:
            return self.redirects[resource]
        if false_if_none:
            return False
        return resource

    def _substitute_match(self, match):
        """ takes the match and substitutes the article link with the redirected article if available """
        resource = self._substitute(match.group(1).replace(" ", "_"), True)
        if not resource:  # if no replacement done
            return match.group(0)
        # otherwise build new link string
        subst = "[["
        subst += resource
        if match.group(3) is not None:  # if alternative text exists
            if not resource == match.group(3):  # check if article link is equal
                subst += match.group(2)
        else:
            subst += "|" + match.group(1)  # add old link text as alternative text
        subst += "]]"
        return subst

    @staticmethod
    def _is_wikimarkup_consistent(text):
        escape_code_left = r'&lt;nowiki&gt;'
        escape_code_right = r'&lt;/nowiki&gt;'
        escaped_bracket_opening = escape_code_left + '[' + escape_code_right
        escaped_bracket_closing = escape_code_left + ']' + escape_code_right
        escaped_opening = text.count(escaped_bracket_opening)
        escaped_closing = text.count(escaped_bracket_closing)
        if text.count('[') - escaped_opening != text.count(']') - escaped_closing:
            return False
        return True

    def _substitute_all(self, string):
        # look for [[linked_article]] or [[linked_article|link_text]]
        regex_wikimarkup = re.compile('\[\[(.+?)(\|(.+?))?\]\]')
        return regex_wikimarkup.sub(self._substitute_match, string)

    def substitute_html(self, string):
        # look for href="wiki/linked_article"
        regex_html = re.compile('(href=\"\/wiki\/)(.*?)(\")')
        return regex_html.sub(self._substitute_match_html, string)

    def _substitute_match_html(self, match):
        if match.group(3) is not None:
            return match.group(1) + self._substitute(match.group(2)) + match.group(3)

        return match.group(0)

    def _yield_paragraphs(self):
        # brackets may not get closed inside a line but inside a paragraph
        with open(self.path_dump, 'rb') as fin:
            # binary mode 'b' enables UTF-8 parsing and prevents Windows from using '\r\n' as line separator
            paragraph = ''
            for line in tqdm(fin):
                paragraph += line
                if line == '\n':
                    yield paragraph
                    paragraph = ''
            yield paragraph

    def substitute_redirects(self):
        # total_lines = line_counting.cached_counter.count_lines(self.path_dump)
        tqdm.write('\n\nSubstituting links in dump...')
        with open(self.path_substituted_dump, 'wb') as fout:
            for paragrapsh in self._yield_paragraphs():
                # if not RedirectsSubstitutor._is_wikimarkup_consistent(paragrapsh):
                #     pass
                # assert RedirectsSubstitutor._is_wikimarkup_consistent(line)
                substituted_paragraph = sub._substitute_all(paragrapsh)
                # assert RedirectsSubstitutor._is_wikimarkup_consistent(substituted_line)
                fout.write(substituted_paragraph)


if __name__ == '__main__':
    sub = RedirectsSubstitutor()
    sub.substitute_redirects()
