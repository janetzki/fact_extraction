#!../venv/bin/python
# -*- coding: utf-8 -*-

from tqdm import tqdm
import re
import csv
import io

total_lines = 930000000  # TODO: replace magic number with line counter
REGEX = re.compile('\[\[(.+?)(\|(.+?))?\]\]')  # look for [[linked_article]] or [[linked_article|link_text]]
REGEX_HTML = re.compile('(href=\"\/wiki\/)(.*?)(\")')  # look for href="wiki/linked_article"


def unicode_csv_reader(utf8_data, dialect=csv.excel, **kwargs):
    csv_reader = csv.reader(utf8_data, dialect=dialect, **kwargs)
    for row in csv_reader:
        yield [unicode(cell, 'utf-8') for cell in row]


class Substitutor:
    def __init__(self, redirects_path='../data/redirects_en.txt', dump_path='../data/enwiki-latest-pages-articles.xml',
                 dump_path_new='../data/enwiki-latest-pages-articles-redirected.xml'):
        self.redirects_path = redirects_path
        self.dump_path = dump_path
        self.dump_path_new = dump_path_new
        self.redirects = {}
        self.delimiter = '#'
        self._load_redirects(redirects_path)

    def _load_redirects(self, redirects_path):
        tqdm.write('\n\nReading redirects file...')
        with open(redirects_path, 'r') as file:
            next(file)
            reader = unicode_csv_reader(file, delimiter=self.delimiter)
            for name, resource in tqdm(reader, total=7340000):  # TODO: replace magic number with line counter
                if name:
                    self.redirects[name] = resource
        tqdm.write('\n')

    def _substitute(self, resource, false_if_none=False):
        if resource in self.redirects:
            return self.redirects[resource]

        if false_if_none:
            return False

        return resource

    def _substitute_all(self, input):
        return REGEX.sub(self._substitute_match, input)

    # takes the match and substitutes the article link with the redirected article if available
    def _substitute_match(self, match):
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

    def _substitute_html(self, input):
        return REGEX_HTML.sub(self._substitute_match_html, input)

    def _substitute_match_html(self, match):
        if match.group(3) is not None:
            return match.group(1) + self._substitute(match.group(2)) + match.group(3)

        return match.group(0)

    def substitute_dump(self):
        tqdm.write('\n\nSubstituting links in dump...')
        with io.open(self.dump_path, 'r', encoding='utf8') as fin, io.open(self.dump_path_new, 'w', encoding='utf8',
                                                                           newline='\n') as fout:
            # newline='\n' prevents Windows from using '\r\n' as line separator which causes inconsistent character
            # offsets in the character index
            for line in tqdm(fin, total=total_lines):
                fout.write(sub._substitute_all(line))


if __name__ == '__main__':
    sub = Substitutor()
    sub.substitute_dump()
