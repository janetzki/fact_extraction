from pattern import Direction
from graphviz import Digraph
import textwrap
import imp

pattern_tool = imp.load_source('pattern_tool', '../storing_tools/pattern_tool.py')
from pattern_tool import PatternTool


class PatternVisualizer(PatternTool):
    def __init__(self, patterns_input_path='../data/patterns_raw.pkl'):
        super(PatternVisualizer, self).__init__(patterns_input_path)
        self.graph = None

    @staticmethod
    def dict_to_string(dictionary):
        reverse_counter = dict()
        for k, v in dictionary.iteritems():
            reverse_counter.setdefault(v, []).append(k)
        return PatternVisualizer.build_displayed_string_from_counter(reverse_counter)

    @staticmethod
    def counter_to_string(title, type_frequencies=None):
        if type_frequencies is not None and len(type_frequencies) > 0:
            return '--- ' + title + ' ---\n' + PatternVisualizer.dict_to_string(type_frequencies)
        else:
            return ''

    def add_node(self, identifier, word_frequencies, subject_type_frequencies=None, object_type_frequencies=None,
                 color="black", shape="ellipse"):
        text = PatternVisualizer.dict_to_string(word_frequencies)
        text += PatternVisualizer.counter_to_string('Subject Types', subject_type_frequencies)
        text += PatternVisualizer.counter_to_string('Object Types', object_type_frequencies)

        self.graph.node(str(identifier), text, color=color, shape=shape)

    def add_edge(self, first_node, second_node, direction, label=""):
        assert direction in [Direction.incoming, Direction.outgoing]
        first, second = str(first_node), str(second_node)
        if direction == Direction.outgoing:
            self.graph.edge(first, second, label=label)
        elif direction == Direction.incoming:
            self.graph.edge(second, first, label=label)

    @staticmethod
    def build_displayed_string_from_counter(reverse_counter):
        res = ''
        reversed_keys = sorted(reverse_counter.keys(), reverse=True)
        for k in reversed_keys:
            v = reverse_counter[k]
            if None in v:
                continue
            res += str(k) + ': '
            words = reduce(lambda x, y: x + ', ' + y, v)
            # inject line breaks
            res += textwrap.fill(words, width=50) + '\n\n'
        return res

    def plot_patterns(self):
        self.logger.print_info('Plotting patterns...')
        for relation_type, pattern in self.relation_type_patterns.iteritems():
            self.graph = Digraph(comment='Pattern Visualizer', format='svg')
            print('Diversity of ' + relation_type + ': ' + str(pattern.calculate_diversity_measure()))
            # print root node
            root = pattern.nodes[pattern.root]
            self.add_node(pattern.root, root.word_frequencies,
                          subject_type_frequencies=pattern.subject_type_frequencies,
                          object_type_frequencies=pattern.object_type_frequencies, color="red",
                          shape="doublecircle")
            # print all remaining nodes
            for id, node in pattern.nodes.iteritems():
                if id == pattern.root:
                    continue  # already rendered
                self.add_node(id, node.word_frequencies)

            # add edges
            for id, node in pattern.nodes.iteritems():
                if not node.dependencies:
                    continue
                first_node = id
                for rel, target in node.dependencies.iteritems():
                    second_node = target
                    direction = rel.direction
                    label = rel.meaning
                    self.add_edge(first_node, second_node, direction, label)

            self.graph.render('visualizations/' + relation_type.split('/')[-1], view=True)


if __name__ == '__main__':
    # PatternVisualizer('../data/patterns_raw.pkl').plot_patterns()
    PatternVisualizer('../data/patterns_cleaned.pkl').plot_patterns()
