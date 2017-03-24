import imp

file_tool = imp.load_source('file_tool', '../storing_tools/file_tool.py')
from file_tool import FileTool


class TypeTool(FileTool):
    """
    Responsible for loading and saving type probabilities
    """

    def __init__(self, patterns_input_path='../data/patterns.pkl', patterns_output_path='../data/patterns.pkl'):
        super(TypeTool, self).__init__(patterns_input_path, patterns_output_path)

    def save_type_probabilities(self):
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
