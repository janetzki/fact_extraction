import imp

config_initializer = imp.load_source('config_initializer', '../config_initializer/config_initializer.py')
from config_initializer import ConfigInitializer

fact_extractor = imp.load_source('fact_extractor', '../pattern_recognition/fact_extractor.py')
from fact_extractor import FactExtractor


class PatternTester(ConfigInitializer):
    def __init__(self, facts_limit, randomize=False, fact_extractor=None):
        self.facts_limit = facts_limit
        self.randomize = randomize

        if fact_extractor is not None:
            self.fact_extractor = fact_extractor
        else:
            self.fact_extractor = FactExtractor.from_config_file()

    @classmethod
    def from_config_file(cls, path='../config.ini'):
        config_parser = cls.get_config_parser(path)
        facts_limit = config_parser.getint('pattern_testing', 'facts_limit')
        randomize = config_parser.getboolean('pattern_testing', 'randomize')
        return cls(facts_limit, randomize)

    def _collect_testing_facts(self):
        pass

    def test_patterns(self):
        pass


if __name__ == '__main__':
    pattern_tester = PatternTester.from_config_file()
    pattern_tester.test_patterns()
