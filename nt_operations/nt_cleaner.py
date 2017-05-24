from logger import Logger
from nt_operations import NTReader
from helper_functions import line_counting, uri_rewriting
from tqdm import tqdm
import codecs
import os

dir_path = os.path.dirname(os.path.abspath(__file__)) + '/'


class NTCleaner(object):
    def __init__(self, nt_path, path_cleaned_nt, filter_relations, assert_complete=False):
        self.nt_path = nt_path
        self.path_cleaned_nt = path_cleaned_nt
        self.filter_relations = filter_relations
        self.assert_complete = assert_complete
        self.logger = Logger.from_config_file()
        self.delimiter = '#'

    def clean_nt(self):
        total_lines = line_counting.cached_counter.count_lines(self.nt_path)
        with codecs.open(self.path_cleaned_nt, 'wb', "utf-8") as fout:
            nt_reader = NTReader(self.nt_path)
            self.logger.print_info('Type extraction...')
            for subject, predicate, type in tqdm(nt_reader.yield_entries(), total=total_lines):
                if self.assert_complete:
                    assert predicate in self.filter_relations
                elif predicate not in self.filter_relations:
                    continue

                subject = uri_rewriting.strip_cleaned_name(subject)
                type = type.replace("owl#", "owl").replace("Wikicat", "W").replace("Yago", "Y")
                type = uri_rewriting.strip_cleaned_name(type)

                assert self.delimiter not in subject and self.delimiter not in type
                fout.write(subject + self.delimiter + type + '\n')


def clean_instance_types(path_types, path_types_cleaned):
    type_relation = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'
    type_cleaner = NTCleaner(path_types, path_types_cleaned, [type_relation], True)
    type_cleaner.clean_nt()


def clean_instance_types_inheritance():
    path_types_inheritance = dir_path + '../data/dbpedia_2016-04.nt'
    path_types_inheritance_cleaned = dir_path + '../data/types_inheritance_en.csv'
    inheritance_relation = 'http://www.w3.org/2000/01/rdf-schema#subClassOf'
    inheritance_cleaner = NTCleaner(path_types_inheritance, path_types_inheritance_cleaned, [inheritance_relation],
                                    False)
    inheritance_cleaner.clean_nt()


def clean_redirects():
    path_redirects = dir_path + '../data/redirects_en.ttl'
    path_redirects_cleaned = dir_path + '../data/redirects_en.csv'
    redirect_relation = 'http://dbpedia.org/ontology/wikiPageRedirects'
    type_cleaner = NTCleaner(path_redirects, path_redirects_cleaned, [redirect_relation], True)
    type_cleaner.clean_nt()


if __name__ == '__main__':
    clean_instance_types(dir_path + '../data/instance_types_en.ttl', dir_path + '../data/types_en.csv')
    clean_instance_types(dir_path + '../data/yago_types.ttl', dir_path + '../data/yago_types.csv')
    clean_redirects()
    clean_instance_types_inheritance()
