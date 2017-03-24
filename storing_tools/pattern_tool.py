import imp

file_tool = imp.load_source('file_tool', '../storing_tools/file_tool.py')
from file_tool import FileTool


class PatternTool(FileTool):
    """
    Responsible for loading and saving patterns
    """

    def __init__(self, patterns_input_path='../data/patterns.pkl', patterns_output_path='../data/patterns.pkl'):
        super(PatternTool, self).__init__(patterns_input_path, patterns_output_path)

    def save_patterns(self):
        """ convenience function """
        self.save()

    @property
    def training_resources(self):
        return self.data[0]

    @training_resources.setter
    def training_resources(self, value):
        self.data = (value, self.data[1])

    @property
    def relation_type_patterns(self):
        return self.data[1]

    @relation_type_patterns.setter
    def relation_type_patterns(self, value):
        self.data = (self.data[0], value)
