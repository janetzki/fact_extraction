from nt_operations import NTReader, NTWriter
import os

dir_path = os.path.dirname(os.path.abspath(__file__)) + '/'


class FactCleaner(object):
    def __init__(self, dbpedia_facts_path=dir_path + '../data/mappingbased_objects_en.ttl',
                 facts_input_path=dir_path + '../results/extracted_facts.nt',
                 facts_output_path=dir_path + '../results/new_facts.nt'):
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
