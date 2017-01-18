import csv
import operator
import imp
from tqdm import tqdm

dbpedia_dump_extractor = imp.load_source('dbpedia_dump_extractor', '../../dbpedia_connector/dbpedia_dump_extractor.py')
from dbpedia_dump_extractor import DBpediaDumpExtractor

uri_rewriting = imp.load_source('uri_rewriting', '../../helper_functions/uri_rewriting.py')
line_counting = imp.load_source('line_counting', '../../helper_functions/line_counting.py')


class WikipediaDumpIndexCreator(object):
    def __init__(self, path_relations='../../data/mappingbased_objects_en.ttl'):
        self.path_relations = path_relations
        self.delimiter = '#'  # '#' is never used as character in page titles

    def _create_text_index(self, source='../../data/enwiki-latest-pages-articles-redirected.xml',
                           destination='../../data/character_index.csv'):
        with open(source, 'r') as fin, open(destination, 'w') as fout:
            total_lines = line_counting.count_lines(source)  # 930,460,404
            character_offset = 0
            page_found = False

            tqdm.write('\n\nCreating index...')
            fout.write('"sep=' + self.delimiter + '"\n')
            for line in tqdm(fin, total=total_lines):
                if page_found:
                    page_found = False
                    title = line[1:-9]
                    fout.write(title + self.delimiter + str(character_offset) + '\n')
                if line[0:8] == "  <page>":
                    page_found = True
                character_offset += len(line)

    def _create_filtered_index(self, source='../../data/character_index.csv',
                               destination='../../data/character_index_filtered.csv'):
        with open(source, 'r') as fin_index, open(destination, 'w') as fout:
            total_lines_relations = line_counting.count_lines(self.path_relations)
            tqdm.write('\n\nCollecting important articles...')
            important_articles = set()
            dbpedia_extractor = DBpediaDumpExtractor(self.path_relations)
            for subject, predicate, object in tqdm(dbpedia_extractor.yield_entries(), total=total_lines_relations):
                important_articles.add(uri_rewriting.strip_cleaned_name(subject))

            total_lines_index = line_counting.count_lines(source)
            tqdm.write('\n\nFiltering important articles...')
            index_reader = csv.reader(fin_index, delimiter=self.delimiter)
            fout.write('"sep=' + self.delimiter + '"\n')
            for line in tqdm(index_reader, total=total_lines_index):
                subject, character_offset = line[0], line[1]
                if subject in important_articles:
                    fout.write(subject + self.delimiter + character_offset + '\n')

    def _create_sorted_index(self, source='../../data/character_index_filtered.csv',
                             destination='../../data/character_index_sorted.csv'):
        """ for index lookup in O(log i) instead of O(i) with i as the size of the index """
        with open(source, 'r') as fin, open(destination, 'w') as fout:
            total_lines = line_counting.count_lines(source)

            tqdm.write('\n\nSorting index...')
            index_reader = csv.reader(fin, delimiter=self.delimiter)
            sorted_list = sorted(index_reader, key=operator.itemgetter(0))
            fout.write('"sep=' + self.delimiter + '"\n')
            for element in tqdm(sorted_list, total=total_lines):
                subject, character_offset = element[0], element[1]
                fout.write(subject + self.delimiter + character_offset + '\n')

    def create_index(self):
        self._create_text_index()
        self._create_filtered_index()
        self._create_sorted_index()


if __name__ == '__main__':
    index_creator = WikipediaDumpIndexCreator()
    index_creator.create_index()
