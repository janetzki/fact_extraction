class Dependency(object):
    def __init__(self, from_node, to_node, meaning):
        self.from_node = from_node
        self.to_node = to_node
        self.meaning = meaning


class DependencyNode(object):
    def __init__(self, tag, word, dependencies):
        self.tag = tag
        self.wordfrequencies = [[word, 1]]
        self.dependencies = dependencies


class Pattern(object):
    def __init__(self, relative_position):
        self.relative_position = relative_position
        self.nodes = {}

    def __repr__(self):
        return 'Pattern()'

    def __str__(self):
        return 'TODO'

    def add_node(self, key, value):
        assert key not in self.nodes
        self.nodes[key] = value
        self.check_consistency(key)

    def check_consistency(self, node):
        for dep in self.nodes[node].dependencies:
            assert dep.from_node == node or dep.to_node == node
