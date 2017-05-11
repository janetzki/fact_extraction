from nt_operations import NTReader
from logger import Logger
from helper_functions import line_counting
from tqdm import tqdm
from bs4 import BeautifulSoup as bs
import unicodecsv as csv
import operator
import os
import io

dir_path = os.path.dirname(os.path.abspath(__file__)) + '/'


class WikipediaDumpIndexCreator(object):
    def __init__(self, path_relations=dir_path + '../data/mappingbased_objects_en.ttl'):
        self.path_relations = path_relations
        self.logger = Logger.from_config_file()
        self.delimiter = '#'  # '#' is never used as character in page titles

    def _create_full_index(self, source=dir_path + '../data/enwiki-latest-pages-articles-redirected.xml',
                           destination=dir_path + '../data/character_index.csv'):
        with open(source, 'rb') as fin, io.open(destination, 'w', encoding='utf8') as fout:
            # binary mode 'b' enables consistent character offset and UTF-8 parsing
            total_lines = line_counting.cached_counter.count_lines(source)  # 930460404
            character_offset = 0
            page_found_offset = None

            self.logger.print_info('Creating index...')
            for line in tqdm(fin, total=total_lines):
                if page_found_offset is not None:
                    title = line[11:-9]
                    soup = bs(title, 'lxml')
                    title = soup.getText()  # parse escaped HTML characters, e.g., '&amp;' -> '&'
                    assert self.delimiter not in title
                    fout.write(title + self.delimiter + str(page_found_offset) + '\n')
                    page_found_offset = None
                if line[0:8] == '  <page>':
                    page_found_offset = character_offset
                character_offset += len(line)

    def _create_filtered_index(self, source=dir_path + '../data/character_index.csv',
                               destination=dir_path + '../data/character_index_filtered.csv'):
        with io.open(source, 'rb') as fin_index, io.open(destination, 'w', encoding='utf8') as fout:
            total_lines_relations = line_counting.cached_counter.count_lines(self.path_relations)
            self.logger.print_info('Collecting important entities...')
            important_articles = set()
            nt_reader = NTReader(self.path_relations)
            for subject, predicate, object in tqdm(nt_reader.yield_cleaned_entry_names(), total=total_lines_relations):
                important_articles.add(subject)

            total_lines_index = line_counting.cached_counter.count_lines(source)
            self.logger.print_info('Filtering important entities...')
            index_reader = csv.reader(fin_index, delimiter=self.delimiter, encoding='utf-8', quoting=csv.QUOTE_NONE)
            for line in tqdm(index_reader, total=total_lines_index):
                subject, character_offset = line
                if subject in important_articles:
                    fout.write(subject + self.delimiter + character_offset + '\n')

    def _create_sorted_index(self, source=dir_path + '../data/character_index_filtered.csv',
                             destination=dir_path + '../data/character_index_sorted.csv'):
        """ for index lookup in O(log i) instead of O(i) with i as the size of the index """
        with io.open(source, 'rb') as fin, io.open(destination, 'w', encoding='utf8') as fout:
            total_lines = line_counting.cached_counter.count_lines(source)

            self.logger.print_info('Sorting index...')
            index_reader = csv.reader(fin, delimiter=self.delimiter, encoding='utf-8')
            sorted_list = sorted(index_reader, key=operator.itemgetter(0))
            for element in tqdm(sorted_list, total=total_lines):
                subject, character_offset = element
                fout.write(subject + self.delimiter + character_offset + '\n')

    def _is_index_consistent_with_dump(self, index_path, dump_path):
        self.logger.print_info('Checking whether index is consistent with dump or not...')
        with io.open(index_path, 'rb') as index_file, open(dump_path, 'rb') as dump_file:
            index_reader = csv.reader(index_file, delimiter=self.delimiter, encoding='utf-8')
            for line in index_reader:
                subject, character_offset = line[0], int(line[1])
                dump_file.seek(character_offset)
                page_begin = dump_file.readline()
                assert page_begin[:8] == '  <page>'  # otherwise the character index does not match the dump

    def create_wikipedia_index(self):
        self._create_full_index()
        self._create_filtered_index()
        self._create_sorted_index()
        self._is_index_consistent_with_dump('../data/character_index_sorted.csv',
                                            '../data/enwiki-latest-pages-articles-redirected.xml')


if __name__ == '__main__':
    index_creator = WikipediaDumpIndexCreator()
    index_creator.create_wikipedia_index()
