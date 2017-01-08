import pickle
import csv
import imp
from tqdm import tqdm
from random import randint
from ConfigParser import SafeConfigParser

pattern_extractor = imp.load_source('pattern_extractor', '../pattern_learning/pattern_extractor.py')
wikipedia_connector = imp.load_source('wikipedia_connector', '../wikipedia_connector/wikipedia_connector.py')
from pattern_extractor import PatternExtractor, Pattern
from wikipedia_connector import WikipediaConnector, TaggedSentence


class FactExtractor(object):
    def __init__(self, articles_limit, use_dump=False, randomize=False, match_threshold=0.005, allow_unknown_entity_types=True,
                 load_path='../data/patterns.pkl',
                 resources_path='../data/mappingbased_objects_en_filtered.csv'):
        self.articles_limit = articles_limit
        self.use_dump = use_dump
        self.randomize = randomize
        self.allow_unknown_entity_types = allow_unknown_entity_types
        self.match_threshold = match_threshold
        self.load_path = load_path
        self.resources_path = resources_path
        self.training_resources = set()
        self.discovery_resources = set()
        self.relation_patterns = {}
        self.wikipedia_connector = WikipediaConnector(self.use_dump)
        self.pattern_extractor = PatternExtractor()

        self._load_patterns()
        self._load_discovery_resources()

    def _load_patterns(self):
        with open(self.load_path, 'rb') as fin:
            self.training_resources, self.relation_patterns = pickle.load(fin)

    def _load_discovery_resources(self):
        with open(self.resources_path, 'r') as f:
            wikireader = csv.reader(f, delimiter=' ', quotechar='"')

            if self.randomize:
                random_offset = randint(0, 10000)  # TODO: get rid off magic number
                for row in wikireader:
                    random_offset -= 1
                    if random_offset == 0:
                        break

            max_results = self.articles_limit
            for row in wikireader:
                if max_results == 0:
                    break
                subject = row[0]
                if subject not in self.training_resources and subject not in self.discovery_resources:
                    self.discovery_resources.add(subject)
                    max_results -= 1

    def _match_pattern_against_relation_patterns(self, pattern, reasonable_relations):
        matching_relations = []
        for relation in reasonable_relations:
            relation_pattern = self.relation_patterns[relation]
            match_score = Pattern.match_patterns(relation_pattern, pattern, self.allow_unknown_entity_types)
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

    def _extract_facts_from_sentences(self, sentences, subject_entity):
        facts = []
        reasonable_relations_for_subject = self._filter_reasonable_relations(subject_entity,
                                                                             self._get_specific_type_frequencies(
                                                                                 'subject'))
        for sentence in tqdm(sentences, total=len(sentences)):
            if sentence.number_of_tokens() > 100:
                continue  # probably too long for stanford tokenizer
            relative_position = sentence.relative_pos
            nl_sentence = sentence.as_string()
            object_addresses_of_links = sentence.addresses_of_links()
            for object_link, object_addresses in object_addresses_of_links.iteritems():
                object_entity = WikipediaConnector.strip_name(object_link)
                reasonable_relations_for_object = self._filter_reasonable_relations(object_entity,
                                                                                    self._get_specific_type_frequencies(
                                                                                        'object'))

                reasonable_relations = reasonable_relations_for_subject & reasonable_relations_for_object
                if not len(reasonable_relations):
                    continue

                pattern = self.pattern_extractor.extract_pattern(nl_sentence, object_addresses, relative_position,
                                                                 subject_entity, object_entity)
                if pattern is None:
                    continue

                matching_relations = self._match_pattern_against_relation_patterns(pattern, reasonable_relations)
                new_facts = [(rel, object_link, score, nl_sentence) for (rel, score) in matching_relations]
                facts.extend(new_facts)
                for fact in new_facts:
                    print('')
                    print(fact)
        return facts

    def extract_facts_from_html(self, html, resource):
        tagged_sentences = TaggedSentence.from_html(html)
        referenced_sentences = filter(lambda sent: sent.contains_any_link(), tagged_sentences)
        subject_entity = WikipediaConnector.strip_name(resource)
        facts = self._extract_facts_from_sentences(referenced_sentences, subject_entity)
        facts = [(resource, rel, obj, score, nl_sentence) for (rel, obj, score, nl_sentence) in facts]
        return facts

    def extract_facts(self):
        facts = []
        tqdm.write('\n\nFact extraction...')
        for resource in self.discovery_resources:
            tqdm.write('\n\n--- ' + resource + ' ----')
            html = self.wikipedia_connector.get_wikipedia_article_html(resource)
            facts.extend(self.extract_facts_from_html(html, resource))
        facts.sort(key=lambda fact: fact[3], reverse=True)
        print('\n\n----- Extracted facts ------')
        for fact in facts:
            print(fact)


def get_input_parameters_from_file(path='../config.ini'):
    config = SafeConfigParser()
    config.read(path)
    use_dump = config.getboolean('general', 'use_dump')
    randomize = config.getboolean('fact_extractor', 'randomize')
    articles_limit = config.getint('fact_extractor', 'articles_limit')
    match_threshold = config.getfloat('fact_extractor', 'match_threshold')
    return use_dump, randomize, articles_limit, match_threshold


def test(fact_extractor):
    print(fact_extractor.extract_facts_from_html(
        'He recently became a professor at the <a href="/wiki/Massachusetts_Institute_of_Technology">MIT</a>.',
          'John Doe'))


if __name__ == '__main__':
    use_dump, randomize, articles_limit, match_threshold = get_input_parameters_from_file()
    fact_extractor = FactExtractor(articles_limit, use_dump, randomize, match_threshold)
    # test(fact_extractor)
    fact_extractor.extract_facts()
