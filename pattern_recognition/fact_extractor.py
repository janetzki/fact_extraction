from __future__ import division
from tqdm import tqdm
from math import ceil
from threading import Thread
from itertools import islice
import imp

pattern_extractor = imp.load_source('pattern_extractor', '../pattern_learning/pattern_extractor.py')
from pattern_extractor import PatternExtractor, Pattern

wikipedia_connector = imp.load_source('wikipedia_connector', '../wikipedia_connector/wikipedia_connector.py')
from wikipedia_connector import WikipediaConnector, TaggedSentence

ttl_parser = imp.load_source('ttl_parser', '../ttl_parsing/ttl_parser.py')
from ttl_parser import TTLParser

pattern_tool = imp.load_source('pattern_tool', '../pattern_tool/pattern_tool.py')
from pattern_tool import PatternTool

uri_rewriting = imp.load_source('uri_rewriting', '../helper_functions/uri_rewriting.py')


class FactExtractor(PatternTool):
    def __init__(self, articles_limit, use_dump=False, randomize=False, match_threshold=0.005, type_matching=True,
                 allow_unknown_entity_types=True, print_interim_results=True, threads=4,
                 resources_path='../data/mappingbased_objects_en.ttl',
                 patterns_input_path='../data/patterns_cleaned.pkl'):
        super(FactExtractor, self).__init__(patterns_input_path)
        self.articles_limit = articles_limit
        self.use_dump = use_dump
        self.allow_unknown_entity_types = allow_unknown_entity_types
        self.match_threshold = match_threshold
        self.type_matching = type_matching
        self.ttl_parser = TTLParser(resources_path, randomize)
        self.wikipedia_connector = WikipediaConnector(self.use_dump)
        self.pattern_extractor = PatternExtractor()
        self.print_interim_results = print_interim_results
        self.discovery_resources = set()
        self.extracted_facts = []
        self.threads = threads

        # self._make_pattern_types_transitive()
        self._load_discovery_resources()

    @classmethod
    def from_config_file(cls):
        config_parser = cls.get_config_parser()
        use_dump = config_parser.getboolean('general', 'use_dump')
        randomize = config_parser.getboolean('fact_extractor', 'randomize')
        articles_limit = config_parser.getint('fact_extractor', 'articles_limit')
        match_threshold = config_parser.getfloat('fact_extractor', 'match_threshold')
        type_matching = config_parser.getboolean('fact_extractor', 'type_matching')
        num_of_treads = config_parser.getint('fact_extractor', 'threads')
        return cls(articles_limit, use_dump, randomize, match_threshold, type_matching)

    def _make_pattern_types_transitive(self):
        for relation, pattern in self.relation_type_patterns.iteritems():
            pattern.subject_type_frequencies = self.pattern_extractor \
                .get_transitive_types(pattern.subject_type_frequencies)
            pattern.object_type_frequencies = self.pattern_extractor \
                .get_transitive_types(pattern.object_type_frequencies)

    def _load_discovery_resources(self):
        article_counter = 0

        self.logger.print_info('Collecting entities for fact extraction...')
        for subject, predicate, object in self.ttl_parser.yield_entries():
            if article_counter == self.articles_limit:
                break
            if subject not in self.training_resources and subject not in self.discovery_resources:
                self.discovery_resources.add(subject)
                article_counter += 1
        self.logger.print_done('Collecting entities for fact extraction completed')

    def _match_pattern_against_relation_type_patterns(self, pattern, reasonable_relations):
        matching_relations = []
        for relation in reasonable_relations:
            relation_pattern = self.relation_type_patterns[relation]
            match_score = Pattern.match_patterns(relation_pattern, pattern, self.type_matching,
                                                 self.allow_unknown_entity_types)
            if match_score >= self.match_threshold:
                matching_relations.append((relation, match_score))
        return matching_relations

    def _filter_reasonable_relations(self, entity, types_of_relations):
        reasonable_relations = set()
        entity_types = self.pattern_extractor.get_entity_types(entity)
        if self.allow_unknown_entity_types and len(entity_types) == 0:
            reasonable_relations = set(types_of_relations.keys())
        else:
            for relation, types in types_of_relations.iteritems():
                assert types is not None
                # Otherwise types were not learned in the training step.
                # In this case you probably have to adjust the config file and rerun the training step.

                if len(entity_types & types) > 0:
                    reasonable_relations.add(relation)
        return reasonable_relations

    def _get_specific_type_frequencies(self, subject_or_object):
        if subject_or_object == 'subject':
            return {relation: pattern.subject_type_frequencies for relation, pattern in
                    self.relation_type_patterns.iteritems()}
        elif subject_or_object == 'object':
            return {relation: pattern.object_type_frequencies for relation, pattern in
                    self.relation_type_patterns.iteritems()}
        else:
            assert False

    def _extract_facts_from_sentences(self, sentences, subject_entity=None):
        facts = []
        if self.type_matching:
            reasonable_relations_for_subject = self._filter_reasonable_relations(subject_entity,
                                                                                 self._get_specific_type_frequencies(
                                                                                     'subject'))
        for sentence in sentences:
            if sentence.number_of_tokens() > 50:
                continue  # probably too long for stanford tokenizer
            relative_position = sentence.relative_pos
            nl_sentence = sentence.as_string()
            object_addresses_of_links = sentence.addresses_of_dbpedia_links()
            for object_link, object_addresses in object_addresses_of_links.iteritems():
                object_entity = uri_rewriting.strip_name(object_link)
                if self.type_matching:
                    reasonable_relations_for_object = self._filter_reasonable_relations(object_entity,
                                                                                        self._get_specific_type_frequencies(
                                                                                            'object'))
                    reasonable_relations = reasonable_relations_for_subject & reasonable_relations_for_object
                else:
                    reasonable_relations = self.relation_type_patterns

                if not len(reasonable_relations):
                    continue

                pattern = self.pattern_extractor.extract_pattern(nl_sentence, object_addresses, relative_position,
                                                                 self.type_matching, subject_entity, object_entity)
                if pattern is None:
                    continue

                matching_relations = self._match_pattern_against_relation_type_patterns(pattern, reasonable_relations)
                new_facts = [(rel, object_link, score, nl_sentence) for (rel, score) in matching_relations]
                facts.extend(new_facts)

                if self.print_interim_results:
                    for fact in new_facts:
                        print('')
                        print(fact)
        return facts

    def extract_facts_from_html(self, html, resource):
        tagged_sentences = TaggedSentence.from_html(html)
        referenced_sentences = filter(lambda sent: sent.contains_any_link(), tagged_sentences)
        if self.type_matching:
            subject_entity = uri_rewriting.strip_name(resource)
        else:
            subject_entity = None
        facts = self._extract_facts_from_sentences(referenced_sentences, subject_entity)
        facts = [(resource, rel, obj, score, nl_sentence) for (rel, obj, score, nl_sentence) in facts]
        return facts

    def extract_facts_from_resource(self, chunk=None):
        self.logger.print_info('--- start fact extraction thread ----')
        if chunk is None:
            chunk = {}
        facts = []
        for resource in chunk:
            wikipedia_resource = uri_rewriting.convert_to_wikipedia_uri(resource)
            self.logger.print_info('--- ' + wikipedia_resource + ' ----')
            html = self.wikipedia_connector.get_wikipedia_article_html(resource)
            temp =  self.extract_facts_from_html(html, resource)
            if temp:
                facts.append(temp)
        if facts:
            self.extracted_facts.extend(facts)

    def _chunks(self, data, size=10000):
        """Yield successive n-sized chunks from l."""
        for i in range(0, len(data), size):
            yield data[i:i + size]

    def extract_facts(self):
        self.logger.print_info('Fact extraction...')
        chunk_size = int(ceil(len(self.discovery_resources) / self.threads))
        threads = []
        # gather resources for each thread
        for chunk in self._chunks(list(self.discovery_resources), chunk_size):
            t = Thread(target=self.extract_facts_from_resource, kwargs={'chunk': chunk})
            threads.append(t)
            # start all threads
        for t in threads:
            t.start()
        # wait for all threads to finish
        for t in threads:
            t.join()
        print(self.extracted_facts)
        if self.extracted_facts:
            self.extracted_facts.sort(key=lambda fact: fact[0][3], reverse=True)
        self.logger.print_done('Fact extraction completed')

    def print_extracted_facts(self):
        self.logger.print_info('----- Extracted facts ------')
        for fact in self.extracted_facts:
            print(fact)

    @property
    def training_relation_types(self):
        return self.relation_type_patterns.keys()

    def set_print_interim_results(self, boolean):
        self.print_interim_results = boolean


if __name__ == '__main__':
    fact_extractor = FactExtractor.from_config_file()
    fact_extractor.extract_facts()
    fact_extractor.print_extracted_facts()
