from nltk.parse.stanford import StanfordDependencyParser

path_to_jar = 'C:\Users\Nirwana\Downloads\stanford-corenlp-full-2016-10-31\stanford-corenlp-3.7.0.jar'
path_to_models_jar = 'C:\Users\Nirwana\Downloads\stanford-corenlp-full-2016-10-31\stanford-corenlp-3.7.0-models.jar'


def find_addresses(parse, search_term_tokens):
    addresses = []
    contiguous_words = 0
    for node in parse.nodes.iteritems():
        dict = node[1]
        word = dict['word']
        if word == search_term_tokens[contiguous_words]:
            contiguous_words += 1
            addresses.append(dict['address'])
            if contiguous_words == len(search_term_tokens):
                return addresses
        else:
            contiguous_words = 0
            addresses = []

    assert (False)  # Should not happen, but program might not crash if assertion is removed.
    return []


def find_related_addresses(parse, search_addresses):
    addresses = []
    for node in parse.nodes.iteritems():
        dict = node[1]
        deps = dict['deps']
        address = dict['address']
        for dep in deps.iteritems():
            type = dep[0]
            if type == 'compound' or type == 'root':
                continue
            related_addresses = dep[1]
            if address in search_addresses:
                addresses.extend(related_addresses)
            elif any(x in search_addresses for x in related_addresses):
                addresses.append(address)
    return addresses


def build_pattern(parse, object_addresses, related_addresses_raw):
    pattern = []
    related_addresses = sorted(set(related_addresses_raw) - set(object_addresses))
    last_address = -1
    object_added = False
    for address in related_addresses:
        if not object_added and address > max(object_addresses):
            pattern.append('[OBJ]')
            object_added = True
        elif last_address > -1 and address - last_address > 1:
            pattern.append('[...]')
        partner_node = parse.nodes[address]
        pattern.append(partner_node['word'])
        last_address = address

    if not object_added:
        pattern.append('[OBJ]')

    return pattern


def find_deep_related_addresses(parse, search_addresses, depth):
    related_addresses = list(search_addresses)
    for i in range(0, depth):
        related_addresses.extend(find_related_addresses(parse, related_addresses))
        related_addresses = sorted(set(related_addresses))
    return related_addresses


def extract_patterns(sentence, object_tokens):
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
    # [parse.tree().pretty_print() for parse in parser.raw_parse('A primary subject of his research later became known as Markov chain and Markov process.')]

    for depth in range(1, 3):
        object_addresses = find_addresses(parse, object_tokens)
        related_addresses = find_deep_related_addresses(parse, object_addresses, depth)
        pattern = build_pattern(parse, object_addresses, related_addresses)
        patterns.append(' '.join(pattern))

    return patterns
