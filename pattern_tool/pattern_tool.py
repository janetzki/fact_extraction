import pickle
import imp

logger = imp.load_source('logger', '../logging/logger.py')
from logger import Logger

config_initializer = imp.load_source('config_initializer', '../config_initializer/config_initializer.py')
from config_initializer import ConfigInitializer


class PatternTool(ConfigInitializer):
    """
    Responsible for loading and saving patterns
    Uses lazy acquisition for better performance
    """

    def __init__(self, patterns_input_path='../data/patterns.pkl', patterns_output_path='../data/patterns.pkl'):
        self._relation_type_patterns = None
        self._training_resources = None
        self.logger = Logger.from_config_file()
        self.patterns_input_path = patterns_input_path
        self.patterns_output_path = patterns_output_path

    def _load_patterns(self):
        print('\n\nPattern loading...')
        with open(self.patterns_input_path, 'rb') as fin:
            self._training_resources, self._relation_type_patterns = pickle.load(fin)

    def save_patterns(self):
        print('\n\nPattern saving...')
        with open(self.patterns_output_path, 'wb') as fout:
            output = self.training_resources, self._relation_type_patterns
            pickle.dump(output, fout, pickle.HIGHEST_PROTOCOL)

    @property
    def relation_type_patterns(self):
        if self._relation_type_patterns is None:
            if self.patterns_input_path is None:
                self._relation_type_patterns = dict()
            else:
                self._load_patterns()
        return self._relation_type_patterns

    @relation_type_patterns.setter
    def relation_type_patterns(self, value):
        self._relation_type_patterns = value

    @property
    def training_resources(self):
        if self._training_resources is None:
            if self.patterns_input_path is None:
                self._training_resources = set()
            else:
                self._load_patterns()
        return self._training_resources

    @training_resources.setter
    def training_resources(self, value):
        self._training_resources = value
