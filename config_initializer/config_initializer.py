import os
from ConfigParser import SafeConfigParser
from shutil import copyfile

dir_path = os.path.dirname(os.path.abspath(__file__)) + '/'


class ConfigInitializer(object):
    """
    Initialize the SafeConfigParser.
    """

    @staticmethod
    def get_config_parser(path=dir_path + '../config.ini'):
        """
        Get a SafeConfigParser that parses a given config file.

        :param path: input path to the config file
        :return: SafeConfigParser for the config file
        """
        ConfigInitializer._generate_config_file_if_missing(path)
        config_parser = SafeConfigParser()
        config_parser.read(path)
        return config_parser

    @staticmethod
    def _generate_config_file_if_missing(dest_path, src_path=dir_path + '../config-default.ini'):
        """
        Make a copy of the default config file if the config file does not exist.

        :param dest_path: output config file
        :param src_path: input default config file
        :return: None
        """
        if not os.path.isfile(dest_path):
            print(dest_path + ' missing, generating new one from ' + src_path)
            copyfile(src_path, dest_path)
