from logger import Logger
from config_initializer import ConfigInitializer
import pickle


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
        self.logger.print_info('Loading from "' + self.input_path + '"...')
        with open(self.input_path, 'rb') as fin:
            self._data = pickle.load(fin)

    def save(self):
        self.logger.print_info('Saving to "' + self.output_path + '"...')
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
