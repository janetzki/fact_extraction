from enum import Enum
from ppretty import ppretty


class Direction(Enum):
    outgoing = 1
    incoming = 2
    loop = 3


class DependencyKey(object):
    def __init__(self, meaning, from_node, to_node, node_addr):
        self.meaning = meaning
        self.direction = DependencyKey.direction(from_node, to_node, node_addr)

    @staticmethod
    def direction(from_node, to_node, node_addr):
        if from_node == node_addr and to_node == node_addr:
            assert False
            return Direction.loop
        if from_node == node_addr:
            return Direction.outgoing
        elif to_node == node_addr:
            return Direction.incoming
        else:
            assert False

    def __hash__(self):
        return hash((self.meaning, self.direction))

    def __eq__(self, other):
        return (self.meaning, self.direction) == (other.meaning, other.direction)

    def __ne__(self, other):
        return not (self == other)


class DependencyNode(object):
    def __init__(self, tag, wordfrequnecies, dependencies=None):
        self.tag = tag
        self.word_frequencies = wordfrequnecies
        if dependencies is None:
            dependencies = {}
        self.dependencies = dependencies

    @classmethod
    def from_word(cls, tag, word):
        return cls(tag, {word: 1})

    @staticmethod
    def _merge_word_frequencies(wf1, wf2):
        return {word: wf1.get(word, 0) + wf2.get(word, 0) for word in set(wf1) | set(wf2)}

    @staticmethod
    def raw_merge(node1, node2):
        tag = node1.tag  # TODO: improve this
        word_frequencies = DependencyNode._merge_word_frequencies(node1.word_frequencies, node2.word_frequencies)
        dependencies = {}
        return DependencyNode(tag, word_frequencies, dependencies)

    def add_word(self, word):
        self.word_frequencies = DependencyNode._merge_word_frequencies(self.word_frequencies, {word: 1})


class Pattern(object):
    def __init__(self, relative_position, root, nodes=None, covered_sentences=1):
        self.relative_position = relative_position
        if nodes is None:
            nodes = {}
        self.nodes = nodes
        self.root = root
        self.covered_sentences = covered_sentences

    def __repr__(self):
        return 'Pattern()'

    def __str__(self):
        return ppretty(self, indent='    ', depth=5, width=40, seq_length=6,
                       show_protected=True, show_private=False, show_static=True,
                       show_properties=True, show_address=True)
        '''position_string = 'Position: ' + '{:10.2f}'.format(self.relative_position)
        nodes_string = 'Nodes: ['
        for node in self.nodes.values():
            nodes_string += str(node) + ', '
        nodes_string = nodes_string[0:-2]
        nodes_string += ']'
        return position_string + ', ' + nodes_string'''

    def add_node(self, key, value):
        assert key not in self.nodes
        self.nodes[key] = value

    def add_dependency_to_node(self, node_addr, key, value):
        assert node_addr in self.nodes.keys()
        dependencies = self.nodes[node_addr].dependencies
        if key not in dependencies.keys():
            dependencies[key] = value
        return dependencies[key]

    @staticmethod
    def insert_nodes(root_node_addr, from_nodes, into_nodes):
        node = from_nodes[root_node_addr]
        new_node = node
        new_node.dependencies = {}
        into_nodes.append(new_node)
        new_node_addr = len(into_nodes) - 1

        for dep in node.dependencies.keys():
            future_node_addr = len(into_nodes)
            Pattern.insert_nodes(node.dependencies[dep], from_nodes, into_nodes)
            into_nodes[new_node_addr].dependencies[dep] = future_node_addr

    @staticmethod
    def merge_nodes(node1_addr, node2_addr, nodes1, nodes2, new_nodes):
        node1 = nodes1[node1_addr]
        node2 = nodes2[node2_addr]
        new_node = DependencyNode.raw_merge(node1, node2)
        new_nodes.append(new_node)
        new_node_addr = len(new_nodes) - 1

        for dep1 in node1.dependencies.keys():
            future_node_addr = len(new_nodes)
            if dep1 in node2.dependencies.keys():
                Pattern.merge_nodes(node1.dependencies[dep1], node2.dependencies[dep1], nodes1, nodes2, new_nodes)
            else:
                Pattern.insert_nodes(node1.dependencies[dep1], nodes1, new_nodes)
            new_nodes[new_node_addr].dependencies[dep1] = future_node_addr

        for dep2 in node2.dependencies.keys():
            future_node_addr = len(new_nodes)
            if dep2 not in node1.dependencies.keys():
                Pattern.insert_nodes(node2.dependencies[dep2], nodes2, new_nodes)
            new_nodes[new_node_addr].dependencies[dep2] = future_node_addr

    @staticmethod
    def merge(pattern1, pattern2):
        new_covered_sentences = pattern1.covered_sentences + pattern2.covered_sentences
        new_relative_position = (
                                    pattern1.covered_sentences * pattern1.relative_position + pattern2.covered_sentences * pattern2.relative_position) / new_covered_sentences
        # assert self.nodes[self.root].tag == pattern.nodes[pattern.root].tag
        new_nodes = []
        Pattern.merge_nodes(pattern1.root, pattern2.root, pattern1.nodes, pattern2.nodes, new_nodes)
        new_pattern = Pattern(new_relative_position, 0, new_nodes, new_covered_sentences)

        print '---------- Pattern Merge ----------'
        print pattern1
        print pattern2
        print new_pattern

        return new_pattern
