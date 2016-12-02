from nltk.parse.stanford import StanfordDependencyParser
from pattern import Pattern, DependencyNode, Dependency

path_to_jar = '..\stanford-corenlp-full-2016-10-31\stanford-corenlp-3.7.0.jar'
path_to_models_jar = '..\stanford-corenlp-full-2016-10-31\stanford-corenlp-3.7.0-models.jar'


def find_main_address(parse, search_term_tokens):
    """ assume that node with more outgoing dependencies is closer too root and return its address """
    contiguous_words = 0
    max_dependencies = 0
    max_address = 0

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
            max_dependencies = 0
            max_address = -1

    print parse
    print search_term_tokens
    assert False
    return -1


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


def build_pattern(parse, graph, object_address, relative_position, depth):
    pattern = Pattern(relative_position)
    visited, queue = set(), [object_address]
    distances = {k: float('inf') for k in parse.nodes.keys()}
    distances[object_address] = 0

    # BFS
    while queue:
        address = queue.pop(0)
        if address not in visited:
            visited.add(address)
            node = graph[address]
            adjacent_addresses = zip(*node)
            adjacent_addresses = set(adjacent_addresses[0] + adjacent_addresses[1])
            for adj in adjacent_addresses:
                distances[adj] = distances[address] + 1
            # cut off distant nodes
            adjacent_addresses = set(filter(lambda x: distances[x] <= depth, adjacent_addresses))

            queue.extend(adjacent_addresses - visited)

            # construct node for pattern and insert it
            dependencies = set()
            for dep in node:
                from_node = dep[0]
                to_node = dep[1]
                meaning = dep[2]
                if from_node == address:
                    partner = to_node
                else:
                    partner = from_node
                if partner in adjacent_addresses:
                    dependencies.add(Dependency(from_node, to_node, meaning))
            properties = parse.nodes[address]
            dep_node = DependencyNode(properties['tag'], properties['word'], dependencies=dependencies)
            pattern.add_node(address, dep_node)

    return pattern


def extract_patterns(sentence, object_tokens, relative_position):
    patterns = []
    if len(sentence) > 1000:
        return '***ERROR: Sentence too long!***'  # otherwise memory error would occur

    object_tokens = filter(lambda x: x != ',', object_tokens)
    parser = StanfordDependencyParser(path_to_jar=path_to_jar, path_to_models_jar=path_to_models_jar)
    result = parser.raw_parse(sentence)
    parse = result.next()

    # tripels = parse.triples()
    # for triple in tripels:
    #    print triple
    # [parse.tree().pretty_print() for parse in parser.raw_parse(sentence)]

    object_address = find_main_address(parse, object_tokens)
    graph = build_graph(parse)

    for depth in range(1, 3):
        pattern = build_pattern(parse, graph, object_address, relative_position, 1)
        patterns.append(pattern)

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

    return patterns


def test():
    sentence = 'Allain Connes won. a very boring prize in 1987.'
    object_tokens = ['prize']
    print(extract_patterns(sentence, object_tokens, 0.0))


if __name__ == '__main__':
    # pass
    test()
