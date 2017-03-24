import imp

file_tool = imp.load_source('file_tool', '../storing_tools/file_tool.py')
from file_tool import FileTool


class TypeLearner(FileTool):
    def __init__(self, output_path='../data/type_probabilities_raw.pkl'):
        super(TypeLearner, self).__init__(None, output_path)

    @classmethod
    def from_config_file(cls):
        config_parser = cls.get_config_parser()
        section = 'type_learner'
        # least_threshold_types = config_parser.getfloat(section, 'least_threshold_types')
        # least_threshold_words = config_parser.getfloat(section, 'least_threshold_words')
        # return cls(least_threshold_types, least_threshold_words)
        return cls()

    def learn_types(self):
        self.logger.print_info('Type learning...')
        # TODO
        self.logger.print_done('Type learning completed.')


if __name__ == '__main__':
    pattern_cleaner = TypeLearner.from_config_file()
    pattern_cleaner.learn_types()
    pattern_cleaner.save()
