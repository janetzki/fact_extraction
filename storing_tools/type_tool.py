import imp

file_tool = imp.load_source('file_tool', '../storing_tools/file_tool.py')
from file_tool import FileTool

# Do not remove this import! It is necessary if pickle has to load a TypePattern from a file.
type_pattern = imp.load_source('type_pattern', '../type_learning/type_pattern.py')
from type_pattern import TypePattern


class TypeTool(FileTool):
    """
    Responsible for loading and saving type patterns
    """

    def __init__(self, patterns_input_path='../data/type_patterns.pkl',
                 patterns_output_path='../data/type_patterns.pkl'):
        super(TypeTool, self).__init__(patterns_input_path, patterns_output_path)

    def save_type_patterns(self):
        """ convenience function """
        self.save()

    @property
    def type_patterns(self):
        """ convenience function """
        return self.data

    @type_patterns.setter
    def type_patterns(self, value):
        """ convenience function """
        self.data = value
