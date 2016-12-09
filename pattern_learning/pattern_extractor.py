import imp
from nltk.parse.stanford import StanfordDependencyParser
import os

# pattern = imp.load_source('pattern', '../pattern learning/pattern.py')
from pattern import Pattern, DependencyKey

path_to_jar = os.path.join('..', 'stanford-corenlp-full-2016-10-31', 'stanford-corenlp-3.7.0.jar')
path_to_models_jar = os.path.join('..', 'stanford-corenlp-full-2016-10-31', 'stanford-corenlp-3.7.0-models.jar')


def find_main_address(parse, search_term_tokens):
    """ assume that node with more outgoing dependencies is closer too root and return its address """
    contiguous_words = 0
    max_dependencies = -1
    max_address = 0

    if len(search_term_tokens) == 0:
        return None

    for node in parse.nodes.iteritems():
        dict = node[1]
        word = dict['word']
        if word == search_term_tokens[contiguous_words]:
            contiguous_words += 1
            dependencies = len(dict['deps'])
            if dependencies > max_dependencies:
                max_dependencies = dependencies
                max_address = dict['address']
            if contiguous_words == len(search_term_tokens):
                return max_address
        else:
            contiguous_words = 0
            max_dependencies = -1
            max_address = None

    print "Error: Search term not found"
    print parse
    print search_term_tokens
    return None
    assert False


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


def extract_pattern(sentence, object_tokens, relative_position):
    depth = 1

    object_tokens = filter(lambda x: x != ',', object_tokens)
    parser = StanfordDependencyParser(path_to_jar=path_to_jar, path_to_models_jar=path_to_models_jar)
    result = parser.raw_parse(sentence)
    parse = result.next()

    # tripels = parse.triples()
    # for triple in tripels:
    #    print triple
    # [parse.tree().pretty_print() for parse in parser.raw_parse(sentence)]

    object_address = find_main_address(parse, object_tokens)
    if object_address is None:
        return None
    graph = build_graph(parse)

    strong_relations = ['xcmp', 'auxpass']
    return build_pattern(parse, graph, object_address, relative_position, depth, strong_relations)

    '''
        for mode in range(0, 2):
            if mode == 0:
                important_relations = None
            else:
                important_relations = ['xcmp', 'auxpass']
            related_addresses = find_deep_related_addresses(parse, object_address, depth, important_relations)
            pattern = build_pattern(parse, object_address, related_addresses, relative_position)
            patterns.append(' '.join(pattern))
    '''


def test():
    sentence = 'Allain Connes won. a very boring prize in 1987.'
    object_tokens = ['prize']
    print(extract_pattern(sentence, object_tokens, 0.0))


if __name__ == '__main__':
    # pass
    test()
