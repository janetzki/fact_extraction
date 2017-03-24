import imp

type_tool = imp.load_source('type_tool', '../storing_tools/type_tool.py')
from type_tool import TypeTool


class PatternMatcher(TypeTool):
    def __init__(self, input_path='../data/type_probabilities_cleaned.pkl'):
        super(PatternMatcher, self).__init__(input_path, None)

    @classmethod
    def from_config_file(cls):
        config_parser = cls.get_config_parser()
        section = 'type_cleaner'
        # least_threshold_types = config_parser.getfloat(section, 'least_threshold_types')
        # least_threshold_words = config_parser.getfloat(section, 'least_threshold_words')
        # return cls(least_threshold_types, least_threshold_words)
        return cls()

    def match_patterns(self, sentence_pattern, learned_pattern):
        pass
