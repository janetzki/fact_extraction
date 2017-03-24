import imp

file_tool = imp.load_source('file_tool', '../storing_tools/file_tool.py')
from file_tool import FileTool


class TypeCleaner(FileTool):
    def __init__(self, input_path='../data/type_probabilities_raw.pkl',
                 output_path='../data/type_probabilities_cleaned.pkl'):
        super(TypeCleaner, self).__init__(input_path, output_path)

    @classmethod
    def from_config_file(cls):
        config_parser = cls.get_config_parser()
        section = 'type_cleaner'
        # least_threshold_types = config_parser.getfloat(section, 'least_threshold_types')
        # least_threshold_words = config_parser.getfloat(section, 'least_threshold_words')
        # return cls(least_threshold_types, least_threshold_words)
        return cls()

    def clean_types(self):
        self.logger.print_info('Type cleaning...')
        # TODO
        self.logger.print_done('Type cleaning completed.')


if __name__ == '__main__':
    pattern_cleaner = TypeCleaner.from_config_file()
    pattern_cleaner.clean_types()
    pattern_cleaner.save()
