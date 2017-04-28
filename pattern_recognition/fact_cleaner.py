import imp

nt_reader = imp.load_source('nt_reader', '../nt_operations/nt_reader.py')
from nt_reader import NTReader

nt_writer = imp.load_source('nt_writer', '../nt_operations/nt_writer.py')
from nt_writer import NTWriter


class FactCleaner(object):
    def __init__(self, dbpedia_facts_path='../data/mappingbased_objects_en.ttl',
                 facts_input_path='../results/extracted_facts.nt',
                 facts_output_path='../results/new_facts.nt'):
        self.dbpedia_nt_reader = NTReader(dbpedia_facts_path)
        self.extracted_facts_nt_reader = NTReader(facts_input_path)
        self.nt_writer = NTWriter(facts_output_path)

    def clean_facts(self):
        dbpedia_facts = set()
        for subject, predicate, object in self.dbpedia_nt_reader.yield_entries():
            dbpedia_facts.add((subject, predicate, object))

        extracted_facts = set()
        for subject, predicate, object in self.extracted_facts_nt_reader.yield_entries():
            extracted_facts.add((subject, predicate, object))

        cleaned_facts = extracted_facts - dbpedia_facts
        self.nt_writer.write_nt(cleaned_facts)


if __name__ == '__main__':
    fact_cleaner = FactCleaner()
    fact_cleaner.clean_facts()
