import imp

config_initializer = imp.load_source('config_initializer', '../config_initializer/config_initializer.py')
from config_initializer import ConfigInitializer

fact_extractor = imp.load_source('fact_extractor', '../pattern_recognition/fact_extractor.py')
from fact_extractor import FactExtractor


class PatternTester(ConfigInitializer):
    def __init__(self, facts_limit, randomize=False, pattern_path='../data/patterns.pkl'):
        self.facts_limit = facts_limit
        self.randomize = randomize
        self.fact_extractor = FactExtractor(pattern_path)

    @classmethod
    def new_from_config_file(cls, path='../config.ini'):
        config_parser = cls.get_config_parser(path)
        facts_limit = config_parser.getint('pattern_testig', 'facts_limit')
        randomize = config_parser.getboolean('pattern_testig', 'use_dump')
        return cls(facts_limit, randomize)

    def test_patterns(self):
        pass


if __name__ == '__main__':
    pattern_tester = PatternTester()
    pattern_tester.test_patterns()
