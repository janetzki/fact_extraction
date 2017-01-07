from __future__ import division
from enum import Enum
from ppretty import ppretty
from collections import Counter
from itertools import dropwhile
import copy


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

    @staticmethod
    def partner_node(from_node, to_node, node_addr):
        direction = DependencyKey.direction(from_node, to_node, node_addr)
        if direction == Direction.outgoing or direction == Direction.loop:
            return to_node
        elif direction == Direction.incoming:
            return from_node
        else:
            assert False

    def __hash__(self):
        return hash((self.meaning, self.direction))

    def __eq__(self, other):
        return (self.meaning, self.direction) == (other.meaning, other.direction)

    def __ne__(self, other):
        return not (self == other)


class DependencyNode(object):
    def __init__(self, tag, word_frequencies, dependencies=None):
        self.tag = tag
        self.word_frequencies = word_frequencies
        if dependencies is None:
            dependencies = {}
        self.dependencies = dependencies

    @classmethod
    def from_word(cls, word, tag=None):
        return cls(tag, {word: 1})

    @staticmethod
    def _merge_dictionaries(dict1, dict2):
        return {word: dict1.get(word, 0) + dict2.get(word, 0) for word in set(dict1) | set(dict2)}

    @staticmethod
    def raw_merge(node1, node2):
        tag = node1.tag  # TODO: improve this
        word_frequencies = DependencyNode._merge_dictionaries(node1.word_frequencies, node2.word_frequencies)
        dependencies = {}
        return DependencyNode(tag, word_frequencies, dependencies)

    def add_word(self, word):
        self.word_frequencies = DependencyNode._merge_dictionaries(self.word_frequencies, {word: 1})


class Pattern(object):
    def __init__(self, relative_position, root, subject_type_frequencies, object_type_frequencies, nodes=None,
                 covered_sentences=1):
        self.relative_position = relative_position
        if nodes is None:
            nodes = {}
        self.nodes = nodes
        self.root = root
        self.covered_sentences = covered_sentences
        self.subject_type_frequencies = subject_type_frequencies
        self.object_type_frequencies = object_type_frequencies

    def __repr__(self):
        return 'Pattern()'

    def __str__(self):
        return ppretty(self, indent='    ', depth=5, width=40, seq_length=6,
                       show_protected=True, show_private=False, show_static=True,
                       show_properties=True, show_address=True)

    def add_word_to_node_or_create_node(self, node_addr, word):
        if node_addr in self.nodes_keys():
            self.nodes[node_addr].add_word(word)
        else:
            self.nodes[node_addr] = DependencyNode.from_word(word)

    def add_dependency_to_node(self, node_addr, key, value):
        assert node_addr in self.nodes_keys()
        dependencies = self.nodes[node_addr].dependencies
        if key not in dependencies.keys():
            dependencies[key] = value
        return dependencies[key]

    def get_node_by_id(self, id):
        return self.nodes[id]

    def calculate_diversity_measure(self):
        """
        Calculates a diversity measure for pattern by dividing the number of unique words
        found in a dependency node by the number of total covered sentences. It neglects the
        compound nodes due to it's absence of expressiveness. Furthermore only nodes of depth 1
        starting at the object are considered.
        """
        num_sentences = self.covered_sentences
        print(num_sentences)
        root_node = self.nodes[self.root]
        if not root_node.dependencies:
            return 0.0
        word_counts = []
        for rel, node_id in root_node.dependencies.iteritems():
            if rel.meaning == 'compound':
                continue
            node = self.nodes[node_id]
            word_count = len(node.word_frequencies)
            word_counts.append(word_count)

        diversity_scores = map(lambda x: x / num_sentences, word_counts)
        return sum(diversity_scores) / len(diversity_scores) if diversity_scores else 0.0

    @staticmethod
    def insert_nodes(root_node_addr, from_nodes, into_nodes):
        node = from_nodes[root_node_addr]
        new_node = copy.deepcopy(node)
        new_node.dependencies = {}
        new_node_addr = len(into_nodes)
        into_nodes[new_node_addr] = new_node

        for dep in node.dependencies.keys():
            future_node_addr = len(into_nodes)
            Pattern.insert_nodes(node.dependencies[dep], from_nodes, into_nodes)
            into_nodes[new_node_addr].dependencies[dep] = future_node_addr

    @staticmethod
    def merge_nodes(node1_addr, node2_addr, nodes1, nodes2, new_nodes):
        node1 = nodes1[node1_addr]
        node2 = nodes2[node2_addr]
        new_node = DependencyNode.raw_merge(node1, node2)
        new_node_addr = len(new_nodes)
        new_nodes[new_node_addr] = new_node

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
    def merge(pattern1, pattern2, assert_valid=False):
        if assert_valid:
            pattern1.assert_is_tree()
            pattern2.assert_is_tree()

        new_covered_sentences = pattern1.covered_sentences + pattern2.covered_sentences
        new_subject_type_frequencies = pattern1.subject_type_frequencies + pattern2.subject_type_frequencies
        new_object_type_frequencies = pattern1.object_type_frequencies + pattern2.object_type_frequencies
        new_relative_position = (pattern1.covered_sentences * pattern1.relative_position +
                                 pattern2.covered_sentences * pattern2.relative_position) / new_covered_sentences
        # assert self.nodes[self.root].tag == pattern.nodes[pattern.root].tag

        new_nodes = {}
        Pattern.merge_nodes(pattern1.root, pattern2.root, pattern1.nodes, pattern2.nodes, new_nodes)
        new_pattern = Pattern(new_relative_position, 0, new_subject_type_frequencies, new_object_type_frequencies,
                              new_nodes, new_covered_sentences)

        if assert_valid:
            # pattern1 and pattern2 still have to be valid (protect against side effects)
            pattern1.assert_is_tree()
            pattern2.assert_is_tree()
            new_pattern.assert_is_tree()

        return new_pattern

    def nodes_keys(self):
        if type(self.nodes) is dict:
            return self.nodes.keys()
        elif type(self.nodes) is list:
            return range(len(self.nodes))
        else:
            assert False

    def assert_is_tree(self):
        visited, queue = set(), [self.root]
        while queue:  # BFS
            node_addr = queue.pop(0)
            assert node_addr not in visited  # forbid loops
            visited.add(node_addr)
            adjacent_addresses = self.nodes[node_addr].dependencies.values()
            assert len(adjacent_addresses) == len(set(adjacent_addresses))  # forbid double edges
            queue.extend(adjacent_addresses)

        assert visited == set(
            self.nodes_keys())  # forbid unconnected nodes or dependencies that don't face from the root

    def total_words_under_node(self, node_addr):
        node = self.nodes[node_addr]
        total_words = sum(node.word_frequencies.values())
        for partner in node.dependencies.values():
            total_words += self.total_words_under_node(partner)
        return total_words

    @staticmethod  # static because pattern might be deleted
    def _delete_node(pattern, node_addr):
        if node_addr == pattern.root:
            return None

        node = pattern.nodes[node_addr]
        for child_addr in node.dependencies.values():
            pattern._delete_node(pattern, child_addr)
        pattern.nodes.pop(node_addr)
        return pattern

    @staticmethod  # static because pattern might be deleted
    def clean_type_frequencies(type_counter, least_threshold):
        for type, frequency in dropwhile(lambda (t, f): f >= least_threshold, type_counter.most_common()):
            del type_counter[type]
        return type_counter

    @staticmethod  # static because pattern might be deleted
    def clean_word_frequencies(pattern, least_threshold, node_addr=None):
        if node_addr is None:
            node_addr = pattern.root
        node = pattern.nodes[node_addr]
        node.word_frequencies = dict(filter(lambda (word, frequency): frequency >= least_threshold,
                                            node.word_frequencies.iteritems()))
        if len(node.word_frequencies) == 0 and node_addr != pattern.root:
            pattern = Pattern._delete_node(pattern, node_addr)
        else:
            for dep, child_addr in node.dependencies.iteritems():
                pattern = Pattern.clean_word_frequencies(pattern, least_threshold, child_addr)
                if child_addr not in pattern.nodes:
                    node.dependencies[dep] = None
            node.dependencies = dict(filter(lambda (dep, addr): addr is not None, node.dependencies.iteritems()))
        return pattern

    @staticmethod  # static because pattern might be deleted
    def clean_pattern(pattern, least_threshold_words=2, least_threshold_types=1):
        pattern.subject_type_frequencies = Pattern.clean_type_frequencies(pattern.subject_type_frequencies,
                                                                          least_threshold_types)
        pattern.object_type_frequencies = Pattern.clean_type_frequencies(pattern.object_type_frequencies,
                                                                         least_threshold_types)
        pattern = Pattern.clean_word_frequencies(pattern, least_threshold_words)
        return pattern

    @staticmethod
    def _match_type_frequencies(type_frequencies1, type_frequencies2, except_second_empty=False):
        '''
        assume that type_frequencies2 contains at most 1 type
        calculate which ratio this type has in type_frequencies1
        :return:    between 0.0 and 1.0
        '''
        if len(type_frequencies2) == 0:
            if except_second_empty:
                return None  # new objects with no type shall not be penalized
            else:
                return 0

        assert len(type_frequencies2) == 1
        type = type_frequencies2.keys()[0]
        type_amount = type_frequencies1[type]
        total = sum(type_frequencies1.values())
        return float(type_amount) / total

    @staticmethod
    def _match_pattern_nodes_unidirectional(pattern1, node1_addr, pattern2, node2_addr, weighting=None):
        '''
        Calculate how much of pattern2 is inside pattern1.
        :return:    between 0.0 and 1.0
        '''
        match_score = 0
        if weighting is None:
            words_under_node = pattern1.total_words_under_node(node1_addr)
            if words_under_node == 0:
                return 0
            weighting = 1.0 / words_under_node
        node1, node2 = pattern1.nodes[node1_addr], pattern2.nodes[node2_addr]
        for dep2 in node2.dependencies.keys():
            if dep2 in node1.dependencies.keys():
                child1_addr, child2_addr = node1.dependencies[dep2], node2.dependencies[dep2]
                child1, child2 = pattern1.nodes[child1_addr], pattern2.nodes[child2_addr]
                if any(word in child1.word_frequencies.keys() for word in child2.word_frequencies.keys()):
                    match_score += sum(child1.word_frequencies.values()) * weighting
                    match_score += Pattern._match_pattern_nodes_unidirectional(pattern1, child1_addr,
                                                                               pattern2, child2_addr, weighting)
        return match_score

    @staticmethod
    def _match_pattern_nodes_bidirectional(pattern1, pattern2):
        return Pattern._match_pattern_nodes_unidirectional(pattern1, pattern1.root, pattern2, pattern2.root) \
               * Pattern._match_pattern_nodes_unidirectional(pattern2, pattern2.root, pattern1, pattern1.root)

    @staticmethod
    def _weighted_arithmetic_mean(data, weights):
        # TODO: Wold geometric mean be more appropriate?
        assert len(data) == len(weights)

        # filter empty values
        weighted_data = zip(data, weights)
        weighted_data = filter(lambda (d, w): d is not None, weighted_data)
        data, weights = zip(*weighted_data)

        # normalize weights
        total_weight = sum(weights)
        normalization_factor = 1 / total_weight
        weights = map(lambda w: w * normalization_factor, weights)

        # calculate mean
        mean = 0
        for i in range(len(data)):
            mean += data[i] * weights[i]
        return mean

    @staticmethod
    def match_patterns(pattern1, pattern2, except_second_empty=False):
        '''
        :return:    between 0.0 and 1.0
        '''
        subject_type_score = Pattern._match_type_frequencies(pattern1.subject_type_frequencies,
                                                             pattern2.subject_type_frequencies,
                                                             except_second_empty)
        if subject_type_score == 0:
            return 0
        object_type_score = Pattern._match_type_frequencies(pattern1.object_type_frequencies,
                                                            pattern2.object_type_frequencies,
                                                            except_second_empty)
        if object_type_score == 0:
            return 0
        node_score = Pattern._match_pattern_nodes_bidirectional(pattern1, pattern2)
        scores = [subject_type_score, object_type_score, node_score]
        weights = [0.25, 0.25, 0.5]
        return Pattern._weighted_arithmetic_mean(scores, weights)
