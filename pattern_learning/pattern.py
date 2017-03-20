from __future__ import division
from enum import Enum
from ppretty import ppretty
from itertools import dropwhile
from collections import Counter
import copy


class Direction(Enum):
    outgoing = 1
    incoming = 2
    loop = 3

    def __repr__(self):
        return 'Direction()'

    def __str__(self):
        if self.value == 1:
            return 'outgoing'
        elif self.value == 2:
            return 'incoming'
        elif self.value == 3:
            return 'loop'
        return '<invalid>'


class DependencyKey(object):
    def __init__(self, meaning, from_node, to_node, node_addr):
        self.meaning = meaning
        self.direction = DependencyKey.direction(from_node, to_node, node_addr)

    def __repr__(self):
        return 'DependencyKey()'

    def __str__(self):
        return '(' + self.meaning + ', ' + str(self.direction) + ')'

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
        if node_addr in self.nodes:
            self.nodes[node_addr].add_word(word)
        else:
            self.nodes[node_addr] = DependencyNode.from_word(word)

    def add_dependency_to_node(self, node_addr, key, value):
        assert node_addr in self.nodes.keys()
        dependencies = self.nodes[node_addr].dependencies
        if key not in dependencies.keys():
            dependencies[key] = value
        return dependencies[key]

    def root_node(self):
        return self.nodes[self.root]

    def calculate_diversity_measure(self):
        """
        Calculates a diversity measure for pattern by dividing the number of unique words
        found in a dependency node by the number of total covered sentences. It neglects the
        compound nodes due to it's absence of expressiveness. Furthermore only nodes of depth 1
        starting at the object are considered.
        """
        num_sentences = self.covered_sentences
        # print(num_sentences)
        if not self.root_node().dependencies:
            return 0.0
        word_counts = []
        for rel, node_id in self.root_node().dependencies.iteritems():
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
    def _merge_nodes(node1_addr, node2_addr, nodes1, nodes2, new_nodes):
        node1 = nodes1[node1_addr]
        node2 = nodes2[node2_addr]
        new_node = DependencyNode.raw_merge(node1, node2)
        new_node_addr = len(new_nodes)
        new_nodes[new_node_addr] = new_node

        for dep1 in node1.dependencies.keys():
            future_node_addr = len(new_nodes)
            if dep1 in node2.dependencies.keys():
                Pattern._merge_nodes(node1.dependencies[dep1], node2.dependencies[dep1], nodes1, nodes2, new_nodes)
            else:
                Pattern.insert_nodes(node1.dependencies[dep1], nodes1, new_nodes)
            new_nodes[new_node_addr].dependencies[dep1] = future_node_addr

        for dep2 in node2.dependencies.keys():
            future_node_addr = len(new_nodes)
            if dep2 not in node1.dependencies.keys():
                Pattern.insert_nodes(node2.dependencies[dep2], nodes2, new_nodes)
                new_nodes[new_node_addr].dependencies[dep2] = future_node_addr

    @staticmethod
    def _merge_type_frequencies(type_frequencies1, type_frequencies2):
        if type_frequencies1 is not None:
            return type_frequencies1 + type_frequencies2
        else:
            return type_frequencies2

    @staticmethod
    def _merge(pattern1, pattern2, assert_valid=False):
        if assert_valid:
            pattern1.assert_is_tree()
            pattern2.assert_is_tree()

        new_covered_sentences = pattern1.covered_sentences + pattern2.covered_sentences
        new_subject_type_frequencies = Pattern._merge_type_frequencies(pattern1.subject_type_frequencies,
                                                                       pattern2.subject_type_frequencies)
        new_object_type_frequencies = Pattern._merge_type_frequencies(pattern1.object_type_frequencies,
                                                                      pattern2.object_type_frequencies)
        new_relative_position = (pattern1.covered_sentences * pattern1.relative_position +
                                 pattern2.covered_sentences * pattern2.relative_position) / new_covered_sentences

        new_nodes = {}
        Pattern._merge_nodes(pattern1.root, pattern2.root, pattern1.nodes, pattern2.nodes, new_nodes)
        new_pattern = Pattern(new_relative_position, 0, new_subject_type_frequencies, new_object_type_frequencies,
                              new_nodes, new_covered_sentences)

        if assert_valid:
            # pattern1 and pattern2 still have to be valid (protect against side effects)
            pattern1.assert_is_tree()
            pattern2.assert_is_tree()
            new_pattern.assert_is_tree()

        return new_pattern

    @staticmethod
    def _intersect_nodes(node1_addr, node2_addr, nodes1, nodes2, new_nodes):
        node1 = nodes1[node1_addr]
        node2 = nodes2[node2_addr]
        current_node_addr = len(new_nodes) - 1

        for dep2 in node2.dependencies.keys():
            if dep2 not in node1.dependencies.keys():
                continue

            child1_addr, child2_addr = node1.dependencies[dep2], node2.dependencies[dep2]
            child1, child2 = nodes1[child1_addr], nodes2[child2_addr]
            new_node = DependencyNode.raw_intersect(child1, child2)
            if len(new_node.word_frequencies) == 0:
                continue

            new_node_addr = len(new_nodes)
            new_nodes[new_node_addr] = new_node
            Pattern._intersect_nodes(node1.dependencies[dep2], node2.dependencies[dep2], nodes1, nodes2, new_nodes)
            new_nodes[current_node_addr].dependencies[dep2] = new_node_addr

    @staticmethod
    def _intersect(pattern1, pattern2):
        new_covered_sentences = min(pattern1.covered_sentences, pattern2.covered_sentences)
        new_subject_type_frequencies = pattern1.subject_type_frequencies & pattern2.subject_type_frequencies
        new_object_type_frequencies = pattern1.object_type_frequencies & pattern2.object_type_frequencies
        new_relative_position = (pattern1.covered_sentences * pattern1.relative_position +
                                 pattern2.covered_sentences * pattern2.relative_position) / new_covered_sentences

        new_nodes = {0: DependencyNode.raw_intersect(pattern1.root_node(), pattern2.root_node())}
        Pattern._intersect_nodes(pattern1.root, pattern2.root, pattern1.nodes, pattern2.nodes, new_nodes)
        new_pattern = Pattern(new_relative_position, 0, new_subject_type_frequencies, new_object_type_frequencies,
                              new_nodes, new_covered_sentences)
        return new_pattern

    def assert_is_tree(self):
        visited, queue = set(), [self.root]
        while queue:  # BFS
            node_addr = queue.pop(0)
            assert node_addr not in visited  # forbid loops
            visited.add(node_addr)
            adjacent_addresses = self.nodes[node_addr].dependencies.values()
            assert len(adjacent_addresses) == len(set(adjacent_addresses))  # forbid double edges
            queue.extend(adjacent_addresses)

        assert visited == \
               set(self.nodes.keys())  # forbid unconnected nodes or dependencies that don't face from the root

    def total_words_under_node(self, node_addr):
        node = self.nodes[node_addr]
        total_words = sum(node.word_frequencies.values())
        for partner in node.dependencies.values():
            total_words += self.total_words_under_node(partner)
        return total_words

    def total_words(self):
        return self.total_words_under_node(self.root)

    def total_words_under_node_with_max_freq(self, node_addr, max_freq):
        node = self.nodes[node_addr]

        total_words = sum(v for k, v in node.word_frequencies.iteritems() if v < max_freq)
        for partner in node.dependencies.values():
            total_words += self.total_words_under_node_with_max_freq(partner, max_freq)
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
    def clean_type_frequencies(type_frequencies, least_threshold):
        if type_frequencies is None:
            return None
        if least_threshold < 1 and len(type_frequencies.most_common(1)) > 0:
            least_threshold = type_frequencies.most_common()[0][1] * least_threshold
        for type, frequency in dropwhile(lambda (t, f): f >= least_threshold, type_frequencies.most_common()):
            del type_frequencies[type]
        return type_frequencies

    @staticmethod  # static because pattern might be deleted
    def clean_nodes_statically(pattern, least_threshold, node_addr=None):
        if node_addr is None:
            node_addr = pattern.root
        node = pattern.nodes[node_addr]
        node.word_frequencies = Counter({k: v for k, v in node.word_frequencies.iteritems() if v >= least_threshold})
        if len(node.word_frequencies) == 0 and node_addr != pattern.root:
            pattern = Pattern._delete_node(pattern, node_addr)
        else:
            for dep, child_addr in node.dependencies.iteritems():
                pattern = Pattern.clean_nodes_statically(pattern, least_threshold, child_addr)
                if child_addr not in pattern.nodes:
                    node.dependencies[dep] = None
            node.dependencies = dict(filter(lambda (dep, addr): addr is not None, node.dependencies.iteritems()))
        return pattern

    @staticmethod  # static because pattern might be deleted
    def clean_nodes(pattern, least_threshold_words):
        pattern.root_node().word_frequencies = {}
        if least_threshold_words < 1:
            lower_bound = pattern.total_words() * least_threshold_words
            least_threshold_words = 2
            while lower_bound <= (
                        pattern.total_words() - pattern.total_words_under_node_with_max_freq(pattern.root,
                                                                                                    least_threshold_words)):
                pattern = Pattern.clean_nodes_statically(pattern, least_threshold_words)
                least_threshold_words += 1
        else:
            pattern = Pattern.clean_nodes_statically(pattern, least_threshold_words)
        return pattern

    @staticmethod  # static because pattern might be deleted
    def clean_pattern(pattern, least_threshold_words=2, least_threshold_types=1):
        pattern.subject_type_frequencies = Pattern.clean_type_frequencies(pattern.subject_type_frequencies,
                                                                          least_threshold_types)
        pattern.object_type_frequencies = Pattern.clean_type_frequencies(pattern.object_type_frequencies,
                                                                         least_threshold_types)
        pattern = Pattern.clean_nodes(pattern, least_threshold_words)
        return pattern

    @staticmethod
    def _match_type_frequencies_unidirectional(type_frequencies1, type_frequencies2, except_second_empty=False):
        '''
        calculate which summed ratio types in type_frequency2 have in type_frequencies1
        :return:    between 0.0 and 1.0
        '''
        if len(type_frequencies2) == 0:
            if except_second_empty:
                return None  # new objects with no type shall not be penalized
            else:
                return 0
        frequency_sum = sum(type_frequencies1.values())
        ratio_sum = 0

        for type, count in type_frequencies2.items():
            if type in type_frequencies1:
                ratio_sum += float(type_frequencies1[type]) / frequency_sum
        return ratio_sum

    @staticmethod
    def _match_type_frequencies(type_frequencies1, type_frequencies2, except_second_empty=False):
        in_order = Pattern._match_type_frequencies_unidirectional(type_frequencies1, type_frequencies2, except_second_empty)
        reversed_order = Pattern._match_type_frequencies_unidirectional(type_frequencies2, type_frequencies1, except_second_empty)
        if in_order is None or reversed_order is None:
            return None
        return in_order * reversed_order

    @staticmethod
    def _match_relative_position(position1, position2):
        '''
        calculate the similarity of relative positions of sentences
        :return: between 0.0 and 1.0
        '''
        return (1 - abs(position1 - position2)) ** 2

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
    def _compute_pattern_intersection_score(pattern1, pattern2):
        intersection = Pattern._intersect(pattern1, pattern2)
        words1, words2, words_intersection = pattern1.total_words(), pattern2.total_words(), intersection.total_words()
        avg_words1 = words1 / pattern1.covered_sentences
        avg_words2 = words2 / pattern2.covered_sentences
        avg_words_intersection = words_intersection / intersection.covered_sentences
        return (avg_words_intersection / avg_words1) * (avg_words_intersection / avg_words2)

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
        normalization_factor = 1.0 / total_weight
        weights = map(lambda w: w * normalization_factor, weights)

        # calculate mean
        mean = 0
        for i in range(len(data)):
            mean += data[i] * weights[i]
        return mean

    @staticmethod
    def match_patterns(pattern1, pattern2, type_matching=True, except_second_empty=False):
        '''
        :return:    between 0.0 and 1.0
        '''
        if type_matching:
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
            position_score = Pattern._match_relative_position(pattern1.relative_position, pattern2.relative_position)
            node_score = Pattern._compute_pattern_intersection_score(pattern1, pattern2)
            scores = [subject_type_score, object_type_score, position_score, node_score]
            # print scores
            weights = [0.25, 0.25, 0.10, 0.40]
            return Pattern._weighted_arithmetic_mean(scores, weights)
        else:
            return Pattern._match_pattern_nodes_bidirectional(pattern1, pattern2)

if __name__ == '__main__':
    test_freq1 = Counter('AAAAABBBC')
    test_freq2 = Counter('CDEAAA')
    print Pattern._match_type_frequencies(test_freq1,test_freq2)

    pos1 = 0.9
    pos2 = 1
    print Pattern._match_relative_position(pos1, pos2)
