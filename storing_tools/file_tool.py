import pickle
import imp

logger = imp.load_source('logger', '../logging/logger.py')
from logger import Logger

config_initializer = imp.load_source('config_initializer', '../config_initializer/config_initializer.py')
from config_initializer import ConfigInitializer


class FileTool(ConfigInitializer):
    """
    Responsible for loading and saving files
    Uses lazy acquisition for better performance
    """

    def __init__(self, input_path, output_path):
        self._data = None
        self.logger = Logger.from_config_file()
        self.input_path = input_path
        self.output_path = output_path

    def _load(self):
        self.logger.print_info('\n\nLoading from "' + self.input_path + '"...')
        with open(self.input_path, 'rb') as fin:
            self._data = pickle.load(fin)

    def save(self):
        self.logger.print_info('\n\nSaving to "' + self.output_path + '"...')
        with open(self.output_path, 'wb') as fout:
            pickle.dump(self._data, fout, pickle.HIGHEST_PROTOCOL)

    @property
    def data(self):
        if self._data is None and self.input_path is not None:
            self._load()
        return self._data

    @data.setter
    def data(self, value):
        self._data = value
