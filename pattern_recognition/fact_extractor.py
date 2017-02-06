#!/usr/bin/python
# encoding=utf8

import pickle
import imp
from tqdm import tqdm
from threading import Thread

config_initializer = imp.load_source('config_initializer', '../config_initializer/config_initializer.py')
from config_initializer import ConfigInitializer

pattern_extractor = imp.load_source('pattern_extractor', '../pattern_learning/pattern_extractor.py')
from pattern_extractor import PatternExtractor, Pattern

wikipedia_connector = imp.load_source('wikipedia_connector', '../wikipedia_connector/wikipedia_connector.py')
from wikipedia_connector import WikipediaConnector, TaggedSentence

ttl_parser = imp.load_source('ttl_parser', '../ttl_parsing/ttl_parser.py')
from ttl_parser import TTLParser

logger = imp.load_source('logger', '../logging/logger.py')
from logger import Logger

uri_rewriting = imp.load_source('uri_rewriting', '../helper_functions/uri_rewriting.py')


class FactExtractor(ConfigInitializer):
    def __init__(self, articles_limit, use_dump=False, randomize=False, match_threshold=0.005, type_matching=True,
                 allow_unknown_entity_types=True, print_interim_results=True,
                 pattern_path='../data/patterns.pkl',
                 resources_path='../data/mappingbased_objects_en.ttl'):
        self.articles_limit = articles_limit
        self.use_dump = use_dump
        self.allow_unknown_entity_types = allow_unknown_entity_types
        self.match_threshold = match_threshold
        self.type_matching = type_matching
        self.pattern_path = pattern_path
        self.ttl_parser = TTLParser(resources_path, randomize)
        self.wikipedia_connector = WikipediaConnector(self.use_dump)
        self.pattern_extractor = PatternExtractor()
        self.print_interim_results = print_interim_results
        self.logger = Logger.from_config_file()
        self.training_resources = set()
        self.discovery_resources = set()
        self.relation_patterns = {}
        self.extracted_facts = []

        self._load_patterns()
        self._make_pattern_types_transitive()
        self._load_discovery_resources()

    @classmethod
    def from_config_file(cls):
        config_parser = cls.get_config_parser()
        use_dump = config_parser.getboolean('general', 'use_dump')
        randomize = config_parser.getboolean('fact_extractor', 'randomize')
        articles_limit = config_parser.getint('fact_extractor', 'articles_limit')
        match_threshold = config_parser.getfloat('fact_extractor', 'match_threshold')
        type_matching = config_parser.getboolean('fact_extractor', 'type_matching')
        return cls(articles_limit, use_dump, randomize, match_threshold, type_matching)

    def _load_patterns(self):
        with open(self.pattern_path, 'rb') as fin:
            self.training_resources, self.relation_patterns = pickle.load(fin)

    def _make_pattern_types_transitive(self):
        for relation, pattern in self.relation_patterns.iteritems():
            pattern.subject_type_frequencies = self.pattern_extractor \
                .get_transitive_types(pattern.subject_type_frequencies)
            pattern.object_type_frequencies = self.pattern_extractor \
                .get_transitive_types(pattern.object_type_frequencies)
            # print pattern.subject_type_frequencies
            # print pattern.object_type_frequencies

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

    def _match_pattern_against_relation_patterns(self, pattern, reasonable_relations):
        matching_relations = []
        for relation in reasonable_relations:
            relation_pattern = self.relation_patterns[relation]
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
                    self.relation_patterns.iteritems()}
        elif subject_or_object == 'object':
            return {relation: pattern.object_type_frequencies for relation, pattern in
                    self.relation_patterns.iteritems()}
        else:
            assert False

    def _extract_facts_from_sentences(self, sentences, subject_entity=None):
        facts = []
        if self.type_matching:
            reasonable_relations_for_subject = self._filter_reasonable_relations(subject_entity,
                                                                                 self._get_specific_type_frequencies(
                                                                                     'subject'))
        for sentence in tqdm(sentences, total=len(sentences)):
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
                    reasonable_relations = self.relation_patterns

                if not len(reasonable_relations):
                    continue

                pattern = self.pattern_extractor.extract_pattern(nl_sentence, object_addresses, relative_position,
                                                                 self.type_matching, subject_entity, object_entity)
                if pattern is None:
                    continue

                matching_relations = self._match_pattern_against_relation_patterns(pattern, reasonable_relations)
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

    def extract_facts_from_resource(self, resource):
        print(started 'thread_patter_fact_ex')
        wikipedia_resource = uri_rewriting.convert_to_wikipedia_uri(resource)
        self.logger.print_info('--- ' + wikipedia_resource + ' ----')
        html = self.wikipedia_connector.get_wikipedia_article_html(resource)
        self.extracted_facts.extend(self.extract_facts_from_html(html, resource))

    def extract_facts(self):
        self.logger.print_info('Fact extraction...')
        threads = []
        # gather resources for each thread
        for resource in self.discovery_resources:
            t = Thread(target=self.extract_facts_from_resource, args=(resource))
            threads.append(t)
        # start threads
        for t in threads:
            t.start()
        # wait until all threads finished
        for t in threads:
            t.join()
        self.extracted_facts.sort(key=lambda fact: fact[3], reverse=True)
        self.logger.print_done('Fact extraction completed')

    def print_extracted_facts(self):
        self.logger.print_info('----- Extracted facts ------')
        for fact in self.extracted_facts:
            print(fact)

    @property
    def training_relationships(self):
        return self.relation_patterns.keys()

    def set_print_interim_results(self, boolean):
        self.print_interim_results = boolean


def test(fact_extractor):
    print(fact_extractor.extract_facts_from_html(
        'He recently became a professor at the <a href="/wiki/Massachusetts_Institute_of_Technology">MIT</a>.',
        'John Doe'))
    print(fact_extractor.extract_facts_from_html(
        'Merkel was educated in Templin and at the <a href="/wiki/University_of_Leipzig" class="mw-redirect" title="University of Leipzig">University of Leipzig</a>, where she studied <a href="/wiki/Physics" title="Physics">physics</a> from 1973 to 1978.',
        'Angela Merkel'))
    print(fact_extractor.extract_facts_from_html(
        'He loves <a href="/wiki/Pyrotechnic">pyrotechnic</a>.',
        'Me'))
    print(fact_extractor.extract_facts_from_html(
        'Some person was born in <a href="/wiki/Braunschweig">Braunschweig</a>.',
        'Me'))
    print(fact_extractor.extract_facts_from_html(
        'Irma Raush was born in <a href="/wiki/Saratov">Saratov</a> on 21 April 1938 into a Volga German family.',
        'Irma Raush'))
    print(fact_extractor.extract_facts_from_html(
        'Born Elinor Isabel Judefind in <a href="/wiki/Baltimore" class="mw-redirect" title="Baltimore, Maryland">Baltimore, Maryland</a> , to parents of French-German descent , Agnew was daughter of William Lee Judefind , a <a href="/wiki/Chemist">chemist</a> , and his wife , the former Ruth Elinor Schafer . ',
        'Judy Agnew'))
    print(fact_extractor.extract_facts_from_html(
        'Her paternal grandfather was a <a href="/wiki/Methodism">Methodist</a> minister . ',
        'Judy Agnew'))


if __name__ == '__main__':
    fact_extractor = FactExtractor.from_config_file()
    # test(fact_extractor)
    fact_extractor.extract_facts()
    fact_extractor.print_extracted_facts()
