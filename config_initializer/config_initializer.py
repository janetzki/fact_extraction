import os.path
from ConfigParser import SafeConfigParser
from shutil import copyfile
from abc import ABCMeta


class abstractclassmethod(classmethod):
    # http://stackoverflow.com/questions/11217878/python-2-7-combine-abc-abstractmethod-and-classmethod
    __isabstractmethod__ = True

    def __init__(self, callable):
        callable.__isabstractmethod__ = True
        super(abstractclassmethod, self).__init__(callable)


class ConfigInitializer(object):
    __metaclass__ = ABCMeta

    @abstractclassmethod
    def from_config_file(cls, path):
        return cls()

    @staticmethod
    def get_config_parser(path='../config.ini'):
        ConfigInitializer._generate_config_file_if_missing(path)
        config_parser = SafeConfigParser()
        config_parser.read(path)
        return config_parser

    @staticmethod
    def _generate_config_file_if_missing(dest_path, src_path='../config-default.ini'):
        if not os.path.isfile(dest_path):
            print(dest_path + ' missing, generating new one from ' + src_path)
            copyfile(src_path, dest_path)
