import imp

type_tool = imp.load_source('type_tool', '../storing_tools/type_tool.py')
from type_tool import TypeTool

pattern = imp.load_source('pattern', '../pattern_learning/pattern.py')
from pattern import Pattern, DependencyNode


class PatternMatcher(TypeTool):
    """
    Compares two patterns with regard to their syntax tree, subject type, object type and relative position in their
    articles. It returns a match score between 0.0 (no match) and 1.0 (complete match).
    """

    def __init__(self, input_path='../data/type_patterns_cleaned.pkl'):
        super(PatternMatcher, self).__init__(input_path, None)
        self.total_facts = sum([type_pattern.facts for type_pattern in self.type_patterns.values()])

    def match_patterns(self, relation_type, learned_pattern, new_pattern, type_matching=True,
                       except_new_pattern_empty=False):
        """
        calculate match score for a large learned pattern and a small pattern from one sentence
        :return:    between 0.0 and 1.0
        """
        if not type_matching:
            return PatternMatcher._compute_pattern_intersection_score(learned_pattern, new_pattern)

        type_pattern = self.type_patterns[relation_type]
        subject_type_score = self._match_type_frequencies(type_pattern.subject_probabilities,
                                                          new_pattern.subject_type_frequencies,
                                                          except_new_pattern_empty)
        if subject_type_score == 0:
            return 0
        object_type_score = self._match_type_frequencies(self.type_patterns[relation_type].object_probabilities,
                                                         new_pattern.object_type_frequencies,
                                                         except_new_pattern_empty)
        if object_type_score == 0:
            return 0
        position_score = PatternMatcher._match_relative_position(learned_pattern.relative_position,
                                                                 new_pattern.relative_position)
        syntax_score = PatternMatcher._compute_pattern_intersection_score(learned_pattern, new_pattern)
        scores = [subject_type_score, object_type_score, position_score, syntax_score]

        subject_type_weight = type_pattern.subject_weighted_probability
        object_type_weight = type_pattern.object_weighted_probability
        relative_position_weight = 0.15
        weights = [subject_type_weight, object_type_weight, relative_position_weight, 1.0]
        match_score = PatternMatcher._weighted_arithmetic_mean(scores, weights)

        # apriori_probability = self.type_patterns[relation_type].facts / float(self.total_facts)
        # match_score = apriori_probability * match_score # makes match scores too low

        assert 0 <= match_score <= 1
        return match_score

    @staticmethod
    def _match_type_frequencies(learned_type_frequencies, new_type_frequencies, except_new_empty=False):
        """
        calculate score that new_type_frequencies belong to relation type of learned type frequencies
        :return:    between 0.0 and 1.0
        """
        if len(new_type_frequencies) == 0:
            if except_new_empty:
                return None  # new objects with no type shall not be penalized
            else:
                return 0

        assert max(new_type_frequencies.itervalues()) <= 1
        # It is considered as a set because it should be retrieved from a single subject / object.
        new_type_frequencies = set(new_type_frequencies)

        types_intersection = new_type_frequencies & set(learned_type_frequencies.keys())
        types_intersection = {type_name: learned_type_frequencies[type_name] for type_name in types_intersection}
        probability_sum = sum(types_intersection.values())
        return probability_sum / len(new_type_frequencies)

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
            PatternMatcher._intersect_nodes(node1.dependencies[dep2], node2.dependencies[dep2], nodes1, nodes2,
                                            new_nodes)
            new_nodes[current_node_addr].dependencies[dep2] = new_node_addr

    @staticmethod
    def _intersect(pattern1, pattern2):
        new_covered_sentences = min(pattern1.covered_sentences, pattern2.covered_sentences)
        new_subject_type_frequencies = pattern1.subject_type_frequencies & pattern2.subject_type_frequencies
        new_object_type_frequencies = pattern1.object_type_frequencies & pattern2.object_type_frequencies
        new_relative_position = None  # relative position makes no sense for intersected pattern

        new_nodes = {0: DependencyNode.raw_intersect(pattern1.root_node(), pattern2.root_node())}
        PatternMatcher._intersect_nodes(pattern1.root, pattern2.root, pattern1.nodes, pattern2.nodes, new_nodes)
        new_pattern = Pattern(new_relative_position, 0, new_subject_type_frequencies, new_object_type_frequencies,
                              new_nodes, new_covered_sentences)
        return new_pattern

    @staticmethod
    def _match_type_frequencies_unidirectional(type_frequencies1, type_frequencies2, except_second_empty=False):

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
    def _match_relative_position(position1, position2):
        """
        calculate the similarity of relative positions of sentences
        :return: between 0.0 and 1.0
        """
        return (1 - abs(position1 - position2)) ** 2

    @staticmethod
    def _compute_pattern_intersection_score(pattern1, pattern2):
        intersection = PatternMatcher._intersect(pattern1, pattern2)
        words1, words2, words_intersection = pattern1.total_words(), pattern2.total_words(), intersection.total_words()
        avg_words1 = float(words1) / pattern1.covered_sentences
        avg_words2 = float(words2) / pattern2.covered_sentences
        avg_words_intersection = float(words_intersection) / intersection.covered_sentences
        syntax_score = (float(avg_words_intersection) / avg_words1) * (float(avg_words_intersection) / avg_words2)
        syntax_score = min(1.0, syntax_score)
        return syntax_score

    @staticmethod
    def _weighted_arithmetic_mean(data, weights):
        # TODO: Would geometric mean be more appropriate?
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


if __name__ == '__main__':
    pattern_matcher = PatternMatcher()
    pos1 = 0.9
    pos2 = 1
    print(PatternMatcher._match_relative_position(pos1, pos2))
