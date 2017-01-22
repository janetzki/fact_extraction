from tqdm import tqdm
import csv
import imp

ttl_parser = imp.load_source('ttl_parser', '../ttl_parsing/ttl_parser.py')
from ttl_parser import TTLParser

line_counting = imp.load_source('line_counting', '../helper_functions/line_counting.py')


class RedirectsExtractor(object):
    def __init__(self, path_redirects='../data/redirects_en.ttl',
                 path_relations='../data/mappingbased_objects_en.ttl',
                 path_extracted_redirects='../data/redirects_en.csv',
                 path_filtered_redirects='../data/redirects_en_filtered.csv'):
        self.path_relations = path_relations
        self.path_redirects = path_redirects
        self.path_extracted_redirects = path_extracted_redirects
        self.path_filtered_redirects = path_filtered_redirects
        self.delimiter = '#'

    def _extract_all_redirects(self):
        with open(self.path_extracted_redirects, 'wb') as fout:
            total_lines_relations = line_counting.count_lines(self.path_relations)
            ttl_parser = TTLParser(self.path_redirects)

            tqdm.write('\n\nExtracting redirects to: ' + self.path_extracted_redirects)
            for subject, predicate, object in tqdm(ttl_parser.yield_cleaned_entry_names(),
                                                   total=total_lines_relations):
                assert self.delimiter not in subject and self.delimiter not in object
                fout.write(subject + self.delimiter + object + '\n')

    def _filter_redirects(self):
        with open(self.path_extracted_redirects, 'rb') as fin_index, open(self.path_filtered_redirects, 'wb') as fout:
            total_lines_relations = line_counting.count_lines(self.path_relations)
            tqdm.write('\n\nCollecting important entities...')
            important_articles = set()
            ttl_parser = TTLParser(self.path_relations)
            for subject, predicate, redirect in tqdm(ttl_parser.yield_cleaned_entry_names,
                                                   total=total_lines_relations):
                # TODO: assert predicate == ''
                important_articles.add(redirect)

            total_lines_index = line_counting.count_lines(self.path_extracted_redirects)
            index_reader = csv.reader(fin_index, delimiter=self.delimiter)
            tqdm.write("\n\nFiltering important entities...")
            for line in tqdm(index_reader, total=total_lines_index):
                subject, object = line
                if subject in important_articles:
                    assert self.delimiter not in subject and self.delimiter not in object
                    fout.write(subject + self.delimiter + object + '\n')

    def extract_redirects(self):
        self._extract_all_redirects()
        # self._filter_redirects()  # not very useful since parsing of Wikipedia dump takes very long for itself


if __name__ == '__main__':
    redirects_extractor = RedirectsExtractor()
    redirects_extractor.extract_redirects()
