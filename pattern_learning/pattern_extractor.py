import imp
import os
from nltk.parse.stanford import StanfordDependencyParser

pattern = imp.load_source('pattern', '../pattern_learning/pattern.py')
from pattern import Pattern, DependencyKey

path_to_jar = os.path.join('..', 'stanford-corenlp-full-2016-10-31', 'stanford-corenlp-3.7.0.jar')
path_to_models_jar = os.path.join('..', 'stanford-corenlp-full-2016-10-31', 'stanford-corenlp-3.7.0-models.jar')


def find_main_address(parse, object_token_addresses):
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


def build_graph(parse):
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


def build_pattern(parse, graph, object_address, relative_position, depth, strong_relations):
    pattern = Pattern(relative_position, object_address)
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
                else:
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
            pattern.add_word_to_node_or_create_node(address_in_pattern, properties['word'])

            for dep in node:
                from_node, to_node, meaning = dep[0:3]
                partner = DependencyKey.partner_node(from_node, to_node, node_addr)
                if partner in adjacent_addresses:
                    key = DependencyKey(meaning, addresses_in_pattern[from_node], addresses_in_pattern[to_node],
                                        address_in_pattern)

                    # address differs if there already is another partner node for this dependency
                    addresses_in_pattern[partner] = pattern.add_dependency_to_node(address_in_pattern, key, partner)

    pattern.assert_is_tree()
    return pattern


def extract_pattern(sentence, object_token_addresses, relative_position, depth=1):
    if len(sentence.strip(' ')) == 0:
        return None
    object_token_addresses = map(lambda addr: addr + 1,
                                 object_token_addresses)  # because TOP token will be inserted at 0

    parser = StanfordDependencyParser(path_to_jar=path_to_jar, path_to_models_jar=path_to_models_jar)
    result = parser.raw_parse(sentence)
    parse = result.next()

    object_address = find_main_address(parse, object_token_addresses)
    if object_address is None:
        return None
    graph = build_graph(parse)

    strong_relations = ['xcmp', 'auxpass']
    return build_pattern(parse, graph, object_address, relative_position, depth, strong_relations)


def test():
    sentence = 'He currently is professor at the Uppsala University.'
    object_tokens = ['University']
    print(extract_pattern(sentence, object_tokens, 0.0))


if __name__ == '__main__':
    # pass
    test()
