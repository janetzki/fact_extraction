import os
import imp
from file_tool import FileTool

dir_path = os.path.dirname(os.path.abspath(__file__)) + '/'

# Do not remove this import! It is necessary as pickle has to load a Pattern from a file.
pattern = imp.load_source('pattern', dir_path + '../pattern_extraction/pattern.py')
from pattern import Pattern


class PatternTool(FileTool):
    """
    Responsible for loading and saving syntactic patterns
    """

    def __init__(self, patterns_input_path=dir_path + '../data/patterns.pkl',
                 patterns_output_path=dir_path + '../data/patterns.pkl'):
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
