import csv
import operator
import imp
from tqdm import tqdm

uri_rewriting = imp.load_source('uri_rewriting', '../helper_functions/uri_rewriting.py')
line_counting = imp.load_source('line_counting', '../helper_functions/line_counting.py')


class WikipediaDumpIndexCreator(object):
    def __init__(self, path_dump='../data/enwiki-latest-pages-articles.xml',
                 path_index='../data/character_index.csv',
                 path_sorted_index='../data/character_index_sorted.csv',
                 path_filtered_index='../data/character_index_sorted.csv',
                 path_relations='../data/mappingbased_objects_en_extracted.csv'
                 # TODO: change to mappingbased_objects_en.tll and adjust code
                 ):
        self.path_dump = path_dump
        self.path_index = path_index
        self.path_sorted_index = path_sorted_index
        self.path_filtered_index = path_filtered_index
        self.path_relations = path_relations
        self.limit = 1e12  # magic number!
        self.delimiter = '#'  # '#' is never used as character in page titles

    def _create_text_index(self):
        total_lines = line_counting.count_lines(self.path_dump)
        with open(self.path_dump, 'r') as fin, open(self.path_index, 'w') as fout:
            line_counter = 0
            character_offset = 0
            page_found = False

            fout.write('"sep=' + self.delimiter + '"\n')

            tqdm.write('\n\nCreating index...')
            for line in tqdm(fin, total=total_lines):
                if page_found:
                    page_found = False
                    title = line[11:-9]
                    fout.write(title + self.delimiter + str(character_offset) + '\n')

                if line[0:8] == "  <page>":
                    page_found = True

                character_offset += len(line)
                line_counter += 1
                if line_counter == self.limit:
                    break

    def _create_sorted_index(self):
        """ for index lookup in O(log i) instead of O(i) with i as the size of the index """
        with open(self.path_filtered_index, 'r') as fin, open(self.path_sorted_index, 'w') as fout:
            indexreader = csv.reader(fin, delimiter=self.delimiter)
            sorted_list = sorted(indexreader, key=operator.itemgetter(0))
            fout.write('"sep=' + self.delimiter + '"\n')
            total_lines = WikipediaDumpIndexCreator(self.path_index)
            tqdm.write('\n\nSorting index...')
            for element in tqdm(sorted_list, total=total_lines):
                fout.write(element[0] + self.delimiter + element[1] + '\n')

    def _create_filtered_index(self):
        with open(self.path_index, 'r') as fin_index, \
                open(self.path_relations, 'r') as fin_relations, \
                open(self.path_filtered_index, 'w') as fout:

            relation_reader = csv.reader(fin_relations, delimiter=' ', quotechar='"')
            important_articles = set()
            total_lines = line_counting.count_lines(self.path_relations)
            tqdm.write('\n\nCollecting important articles...')
            for line in tqdm(relation_reader, total=total_lines):
                important_articles.add(uri_rewriting.strip_cleaned_name(line[0]))

            index_reader = csv.reader(fin_index, delimiter=self.delimiter)
            total_lines = line_counting.count_lines(self.path_index)
            # fout.write('"sep=' + delimiter + '"\n')
            tqdm.write('\n\nFiltering importatnt articles...')
            for line in tqdm(index_reader, total=total_lines):
                if line[0] in important_articles:
                    fout.write(line[0] + self.delimiter + line[1] + '\n')

    def create_index(self):
        self._create_text_index()
        self._create_filtered_index()
        self._create_sorted_index()


if __name__ == '__main__':
    index_creator = WikipediaDumpIndexCreator()
    index_creator.create_index()
