import os
from ontology_building import EntityTypes
from pattern import Pattern
from dependency_key import DependencyKey
from collections import Counter
from nltk.parse.stanford import StanfordDependencyParser

dir_path = os.path.dirname(os.path.abspath(__file__)) + '/'
path_to_jar = dir_path + '../stanford-corenlp-full-2016-10-31/stanford-corenlp-3.7.0.jar'
path_to_models_jar = dir_path + '../stanford-corenlp-full-2016-10-31/stanford-corenlp-3.7.0-models.jar'
stanford_parser = StanfordDependencyParser(path_to_jar=path_to_jar, path_to_models_jar=path_to_models_jar)


class PatternExtractor(object):
    def __init__(self, type_learning=True):
        self.parser = stanford_parser
        if type_learning:
            self.instance_types = EntityTypes()

    @staticmethod
    def _find_main_address(parse, object_token_addresses):
        """ assume that node with more outgoing dependencies is closer too root and return its address """
        max_dependencies = -1
        max_address = None

        if len(object_token_addresses) == 0:
            return None

        for address in object_token_addresses:
            node = parse.nodes[address]
            dependencies = len(node['deps'])
            if dependencies > max_dependencies:
                max_dependencies = dependencies
                max_address = node['address']

        return max_address

    @staticmethod
    def _build_graph_from_dependeny_parse(parse):
        """ return non-directional graph as adjacency list """
        graph = {k: set() for k in parse.nodes.keys()}
        for node in parse.nodes.iteritems():
            properties = node[1]
            deps = properties['deps']
            from_node = properties['address']
            for dep in deps.iteritems():
                meaning = dep[0]
                related_addresses = dep[1]
                for to_node in related_addresses:
                    edge = (from_node, to_node, meaning)
                    graph[from_node].add(edge)
                    graph[to_node].add(edge)

        return graph

    @staticmethod
    def _build_pattern(parse, graph, object_address, relative_position, depth, strong_relations, subject_types,
                       object_types):
        new_pattern = Pattern(relative_position, object_address, subject_types, object_types)
        visited, queue = set(), [object_address]
        distances = {k: float('inf') for k in parse.nodes.keys()}
        distances[object_address] = 0
        addresses_in_pattern = {k: k for k in parse.nodes.keys()}

        # BFS
        while queue:
            node_addr = queue.pop(0)
            if node_addr not in visited:
                visited.add(node_addr)
                node = graph[node_addr]

                normal_adjacent_addresses = set()
                strong_adjacent_addresses = set()
                for dep in node:
                    from_node, to_node, meaning = dep[0:3]
                    partner = DependencyKey.partner_node(from_node, to_node, node_addr)
                    if meaning in strong_relations:
                        strong_adjacent_addresses.add(partner)
                    elif meaning != 'root':
                        normal_adjacent_addresses.add(partner)

                # don't go back towards root
                normal_adjacent_addresses -= visited
                strong_adjacent_addresses -= visited

                for adj in normal_adjacent_addresses:
                    distances[adj] = distances[node_addr] + 1
                for adj in strong_adjacent_addresses:
                    distances[adj] = distances[node_addr]

                # cut off distant nodes
                assert len(normal_adjacent_addresses & strong_adjacent_addresses) == 0
                adjacent_addresses = normal_adjacent_addresses | strong_adjacent_addresses
                adjacent_addresses = set(filter(lambda x: distances[x] <= depth, adjacent_addresses))

                queue.extend(adjacent_addresses)

                # construct node for pattern and insert it (if not yet existing, otherwise add only word string)
                properties = parse.nodes[node_addr]
                address_in_pattern = addresses_in_pattern[node_addr]
                new_pattern.add_word_to_node_or_create_node(address_in_pattern, properties['word'])

                for dep in node:
                    from_node, to_node, meaning = dep[0:3]
                    partner = DependencyKey.partner_node(from_node, to_node, node_addr)
                    if partner in adjacent_addresses:
                        key = DependencyKey(meaning, addresses_in_pattern[from_node], addresses_in_pattern[to_node],
                                            address_in_pattern)

                        # address differs if there already is another partner node for this dependency
                        addresses_in_pattern[partner] = new_pattern.add_dependency_to_node(address_in_pattern, key,
                                                                                           partner)

        new_pattern.assert_is_tree()
        return new_pattern

    def extract_pattern(self, sentence, object_token_addresses, relative_position, type_extraction=False,
                        subject_entity=None, object_entity=None, depth=2):
        if len(sentence.strip(' ')) == 0:
            return None
        object_token_addresses = map(lambda addr: addr + 1,
                                     object_token_addresses)  # because TOP token will be inserted at 0

        result = self.parser.raw_parse(sentence)
        parse = result.next()

        object_address = PatternExtractor._find_main_address(parse, object_token_addresses)
        assert object_address is not None  # otherwise the word tokenization is (still) inconsistent (Issue #37)

        graph = PatternExtractor._build_graph_from_dependeny_parse(parse)

        if type_extraction and self.instance_types:
            assert subject_entity is not None and object_entity is not None
            subject_types = self.instance_types.count_types(subject_entity)
            object_types = self.instance_types.count_types(object_entity)
        else:
            subject_types = Counter()
            object_types = Counter()

        strong_relations = ['xcmp', 'auxpass']
        return PatternExtractor._build_pattern(parse, graph, object_address, relative_position, depth, strong_relations,
                                               subject_types, object_types)

    def get_entity_types(self, entity):
        return self.instance_types.count_types(entity)

    def get_transitive_types(self, types):
        return self.instance_types.get_transitive_types(types)


def test():
    pattern_extractor = PatternExtractor()
    sentence = 'He currently is professor at the Uppsala University.'
    object_tokens = [7]
    print(pattern_extractor.extract_pattern(sentence, object_tokens, 0.0))


if __name__ == '__main__':
    test()
