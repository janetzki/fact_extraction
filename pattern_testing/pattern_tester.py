import imp

fact_extractor = imp.load_source('fact_extractor', '../pattern_recognition/fact_extractor.py')
from fact_extractor import FactExtractor


class PatternTester(object):
    def __init__(self, pattern_path='../data/patterns.pkl'):
        self.fact_extractor = pattern_path

    def load_patterns(self):
        pass

    def test_patterns(self):
        pass


if __name__ == '__main__':
    pattern_tester = PatternTester()
    pattern_tester.test_patterns()
