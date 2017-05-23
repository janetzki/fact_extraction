import os
import imp
from file_tool import FileTool

dir_path = os.path.dirname(os.path.abspath(__file__)) + '/'

# Do not remove this import! It is necessary as pickle has to load Patterns from a file.
pattern = imp.load_source('pattern', dir_path + '../pattern_extraction/pattern.py')
from pattern import Pattern

# Do not remove this import! It is necessary as pickle has to load DependencyKeys from a file.
dependency_key = imp.load_source('dependency_key', dir_path + '../pattern_extraction/dependency_key.py')


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
    # save and load small pattern
    pattern_path = dir_path + '../data/patterns_unittest.pkl'
    pattern_tool = PatternTool(None, pattern_path)
    pattern_tool.save_patterns()
    pattern_tool = PatternTool(pattern_path, pattern_path)
    pattern_tool.save_patterns()

    # load large pattern
    pattern_path = dir_path + '../data/patterns_cleaned.pkl'
    pattern_tool = PatternTool(pattern_path)
    pattern_tool._initialize_data_if_empty()


if __name__ == '__main__':
    test_pattern_tool()
