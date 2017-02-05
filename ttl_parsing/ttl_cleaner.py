from tqdm import tqdm
import imp

ttl_parser = imp.load_source('ttl_parser', '../ttl_parsing/ttl_parser.py')
from ttl_parser import TTLParser

line_counting = imp.load_source('line_counting', '../helper_functions/line_counting.py')
uri_rewriting = imp.load_source('uri_rewriting', '../helper_functions/uri_rewriting.py')


class TTLCleaner(object):
    def __init__(self, path_ttl, path_cleaned_ttl, filter_relations, assert_complete=False):
        self.path_ttl = path_ttl
        self.path_cleaned_ttl = path_cleaned_ttl
        self.filter_relations = filter_relations
        self.assert_complete = assert_complete
        self.delimiter = '#'

    def clean_ttl(self):
        total_lines = line_counting.cached_counter.count_lines(self.path_ttl)
        with open(self.path_cleaned_ttl, 'wb') as fout:
            ttl_parser = TTLParser(self.path_ttl)
            tqdm.write('\n\nType extraction...')
            for subject, predicate, type in tqdm(ttl_parser.yield_entries(), total=total_lines):
                if self.assert_complete:
                    assert predicate in self.filter_relations
                elif predicate not in self.filter_relations:
                    continue

                subject = uri_rewriting.strip_cleaned_name(subject)
                type = type.replace("owl#", "owl")
                type = uri_rewriting.strip_cleaned_name(type)
                assert self.delimiter not in subject and self.delimiter not in type
                fout.write(subject + self.delimiter + type + '\n')


def clean_instance_types():
    path_types = '../data/instance_types_en.ttl'
    path_types_cleaned = '../data/types_en.csv'
    type_relation = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'
    type_cleaner = TTLCleaner(path_types, path_types_cleaned, [type_relation], True)
    type_cleaner.clean_ttl()


def clean_instance_types_inheritance():
    path_types_inheritance = '../data/dbpedia_2016-04.nt'
    path_types_inheritance_cleaned = '../data/types_inheritance_en.csv'
    inheritance_relation = 'http://www.w3.org/2000/01/rdf-schema#subClassOf'
    inheritance_cleaner = TTLCleaner(path_types_inheritance, path_types_inheritance_cleaned, [inheritance_relation],
                                     False)
    inheritance_cleaner.clean_ttl()


def clean_redirects():
    path_redirects = '../data/redirects_en.ttl'
    path_redirects_cleaned = '../data/redirects_en.csv'
    redirect_relation = 'http://dbpedia.org/ontology/wikiPageRedirects'
    type_cleaner = TTLCleaner(path_redirects, path_redirects_cleaned, [redirect_relation], True)
    type_cleaner.clean_ttl()


if __name__ == '__main__':
    clean_instance_types()
    clean_instance_types_inheritance()
    clean_redirects()