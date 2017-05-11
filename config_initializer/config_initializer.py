import os
from ConfigParser import SafeConfigParser
from shutil import copyfile

dir_path = os.path.dirname(os.path.abspath(__file__)) + '/'


class ConfigInitializer(object):
    @staticmethod
    def get_config_parser(path=dir_path + '../config.ini'):
        ConfigInitializer._generate_config_file_if_missing(path)
        config_parser = SafeConfigParser()
        config_parser.read(path)
        return config_parser

    @staticmethod
    def _generate_config_file_if_missing(dest_path, src_path=dir_path + '../config-default.ini'):
        if not os.path.isfile(dest_path):
            print(dest_path + ' missing, generating new one from ' + src_path)
            copyfile(src_path, dest_path)
