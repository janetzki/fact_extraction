from pattern import Pattern, Direction
from graphviz import Digraph
import pickle
import argparse
import textwrap

def add_node(graph, identifier, data, color="black", shape="ellipse"):
    reverse_counter = dict()
    for k, v in data.iteritems():
        reverse_counter.setdefault(v, []).append(k)
    text = build_displayed_string_from_counter(reverse_counter)
    graph.node(str(identifier), text, color=color, shape=shape)
    return graph

def add_edge(graph, first_node, second_node, direction, label=""):
    assert direction in [Direction.incoming, Direction.outgoing]
    first, second = str(first_node), str(second_node)
    if direction == Direction.outgoing:
        dot.edge(first, second, label=label)
    elif direction == Direction.incoming:
        dot.edge(second, first, label=label)
    return graph

def build_displayed_string_from_counter(reverse_counter):
    res = ""
    for k, v in reverse_counter.iteritems():
        if None in v:
            continue
        res += str(k) + ' occurence: \n'
        words = reduce(lambda x, y: x + ', ' + y, v)
        # inject line breaks
        res += textwrap.fill(words, width=50) + '\n'
    return res



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", type=str,
                        help="path to stored pickle data")
    args = parser.parse_args()
    path = args.p if args.p else "../data/patterns.pkl"

    with open (path, 'rb')as f:
        patterns = pickle.load(f)

    for prop in list(patterns[1].iterkeys()):
        dot = Digraph(comment='Pattern Visualizer', format='svg')
        pattern = patterns[1][prop]

        # print root node
        root = pattern.get_node_by_id(pattern.root)
        add_node(dot, pattern.root, root.word_frequencies, color="red", shape="doublecircle")
        # print all remaining nodes
        for id, node in enumerate(pattern.nodes):
            if id == pattern.root:
                continue #  already rendered
            add_node(dot, id, node.word_frequencies)

        # add edges
        for id, node in enumerate(pattern.nodes):
            if not node.dependencies:
                continue
            first_node = id
            for rel, target in node.dependencies.iteritems():
                second_node = target
                direction = rel.direction
                label = rel.meaning
                add_edge(dot, first_node, second_node, direction, label)



        dot.render('visualizations/' + prop.split('/')[-1], view=True)
