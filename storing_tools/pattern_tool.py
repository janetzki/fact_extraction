from collections import Counter
import imp

file_tool = imp.load_source('file_tool', '../storing_tools/file_tool.py')
from file_tool import FileTool


class PatternTool(FileTool):
    """
    Responsible for loading and saving syntactic patterns
    """

    def __init__(self, patterns_input_path='../data/patterns.pkl', patterns_output_path='../data/patterns.pkl'):
        super(PatternTool, self).__init__(patterns_input_path, patterns_output_path)

    def save_patterns(self):
        self._initialize_data_if_empty()
        self.save()

    def _initialize_data_if_empty(self):
        if self.data is None:
            self.data = (set(), dict())

    @property
    def training_resources(self):
        self._initialize_data_if_empty()
        return self.data[0]

    @training_resources.setter
    def training_resources(self, value):
        self._initialize_data_if_empty()
        self.data = (value, self.data[1])

    @property
    def relation_type_patterns(self):
        self._initialize_data_if_empty()
        return self.data[1]

    @relation_type_patterns.setter
    def relation_type_patterns(self, value):
        self._initialize_data_if_empty()
        self.data = (self.data[0], value)


def test_pattern_tool():
    pattern_tool = PatternTool(None)
    # pattern = Pattern(0.0, 0, Counter(), Counter())
    # pattern_tool.relation_type_patterns = {'almaMater': pattern}
    pattern_tool.save_patterns()


if __name__ == '__main__':
    test_pattern_tool()
