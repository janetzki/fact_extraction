from logger import Logger
from helper_functions import line_counting
from tqdm import tqdm
import re
import csv
import os
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

dir_path = os.path.dirname(os.path.abspath(__file__)) + '/'


class RedirectsSubstitutor:
    """
    Substitute links in Wikipedia dump with their final target if they point to a redirect page.
    """

    def __init__(self, path_dump=dir_path + '../data/enwiki-latest-pages-articles.xml',
                 path_redirects=dir_path + '../data/redirects_en.csv',
                 path_substituted_dump=dir_path + '../data/enwiki-latest-pages-articles-redirected.xml'):
        """
        Specify where the original Wikipedia dump is, where the redirects are saved, and where the Wikipedia dump with
        inplace redirects dump shall be saved.

        :param path_dump: input original Wikipedia dump
        :param path_redirects: input Wikipedia redirects file
        :param path_substituted_dump: output Wikipedia dump with inplace redirects
        """
        self.path_dump = path_dump
        self.path_substituted_dump = path_substituted_dump
        self.logger = Logger.from_config_file()
        self.redirects = {}
        self.delimiter = '#'
        self._load_redirects(path_redirects)

    def _load_redirects(self, redirects_path):
        """
        Load the Wikipedia redirects from a file.

        :param redirects_path: input file containing redirects
        :return: None
        """
        total_lines = line_counting.cached_counter.count_lines(redirects_path)
        self.logger.print_info('Reading redirects file...')
        with open(redirects_path, 'rb') as fin:
            reader = csv.reader(fin, delimiter=self.delimiter)
            for name, resource in tqdm(reader, total=total_lines):
                self.redirects[name] = resource

    def _substitute(self, resource, false_if_none=False):
        """
        Get final target of a resource name or check whether it can be redirected.

        :param resource: resource name
        :param false_if_none: boolean whether False shall be returned if resource is already final target
        :return: final target of the resource (or False if already final target)
        """
        if resource in self.redirects:
            return self.redirects[resource]
        if false_if_none:
            return False
        return resource

    @staticmethod
    def _is_wikimarkup_consistent(text):
        """
        Check whether the Wikimarkup contains the same amount of square brackets open and close.

        :param text: Wikimarkup text
        :return: boolean whether the Wikimarkup is consistent or not
        """
        escape_code_left = r'&lt;nowiki&gt;'
        escape_code_right = r'&lt;/nowiki&gt;'
        escaped_bracket_opening = escape_code_left + '[' + escape_code_right
        escaped_bracket_closing = escape_code_left + ']' + escape_code_right
        escaped_opening = text.count(escaped_bracket_opening)
        escaped_closing = text.count(escaped_bracket_closing)
        return text.count('[') - escaped_opening == text.count(']') - escaped_closing

    def _substitute_all(self, string):
        """
        Substitute all links in the Wikimarkup string with their final targets.
        Look for '[[linked_article]]' and '[[linked_article|link_text]]'.

        :param string: Wikimarkup text
        :return: Wikimarkup text only containing links to final targets
        """
        regex_wikimarkup = re.compile('\[\[(.+?)(\|(.+?))?\]\]')
        return regex_wikimarkup.sub(self._substitute_match, string)

    def _substitute_match(self, match):
        """
        Take the matched Wikimarkup link and substitute the article link with the final target if available.

        :param match: matched Wikimarkup link
        :return: substituted Wikimarkup link
        """
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

    def substitute_html(self, string):
        """
        Substitute all links in the HTML string with their final targets.
        Look for 'href="wiki/linked_article"'.

        :param string: HTML text
        :return: HTML text only containing links to final targets
        """
        regex_html = re.compile('(href=\"\/wiki\/)(.*?)(\")')
        return regex_html.sub(self._substitute_match_html, string)

    def _substitute_match_html(self, match):
        """
        Take the matched HTML link and substitute the article link with the final target if available.

        :param match: matched HTML link
        :return: substituted HTML link
        """
        if match.group(3) is not None:
            return match.group(1) + self._substitute(match.group(2)) + match.group(3)
        return match.group(0)

    def _yield_paragraphs(self):
        """
        Yield each paragraph of the original Wikipedia dump.

        :yield: paragraphs
        """
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
        """
        Substitute links in Wikipedia dump with their final target if they point to a redirect page.

        :return: None
        """
        # total_lines = line_counting.cached_counter.count_lines(self.path_dump)
        self.logger.print_info('Substituting links in dump...')
        with open(self.path_substituted_dump, 'wb') as fout:
            for paragraphs in self._yield_paragraphs():
                # if not RedirectsSubstitutor._is_wikimarkup_consistent(paragraphs):
                #     pass
                # assert RedirectsSubstitutor._is_wikimarkup_consistent(line)
                substituted_paragraph = sub._substitute_all(paragraphs)
                # assert RedirectsSubstitutor._is_wikimarkup_consistent(substituted_line)
                fout.write(substituted_paragraph)


if __name__ == '__main__':
    sub = RedirectsSubstitutor()
    sub.substitute_redirects()
