from collections import Counter


class DependencyNode(object):
    def __init__(self, word_frequencies, dependencies=None):
        self.word_frequencies = word_frequencies
        if dependencies is None:
            dependencies = {}
        self.dependencies = dependencies

    @classmethod
    def from_word(cls, word):
        return cls(Counter({word: 1}))

    @staticmethod
    def raw_merge(node1, node2):
        word_frequencies = node1.word_frequencies + node2.word_frequencies
        dependencies = {}
        return DependencyNode(word_frequencies, dependencies)

    @staticmethod
    def raw_intersect(node1, node2):
        word_frequencies = node1.word_frequencies & node2.word_frequencies
        dependencies = {}
        return DependencyNode(word_frequencies, dependencies)

    def add_word(self, word):
        self.word_frequencies[word] += 1
