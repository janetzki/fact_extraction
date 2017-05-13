from file_tool import FileTool
import os
import imp

dir_path = os.path.dirname(os.path.abspath(__file__)) + '/'

# Do not remove this import! It is necessary as pickle has to load a TypePattern from a file.
type_pattern = imp.load_source('type_pattern', dir_path + '../type_learning/type_pattern.py')


class TypeTool(FileTool):
    """
    Responsible for loading and saving type patterns
    """

    def __init__(self, patterns_input_path=dir_path + '../data/type_patterns.pkl',
                 patterns_output_path=dir_path + '../data/type_patterns.pkl'):
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


if __name__ == '__main__':
    type_tool = TypeTool(dir_path + '../data/type_patterns_cleaned.pkl')
    type_patterns = type_tool.type_patterns
