import imp
from termcolor import colored

config_initializer = imp.load_source('config_initializer', '../config_initializer/config_initializer.py')
from config_initializer import ConfigInitializer


class Logger(ConfigInitializer):
    def __init__(self, warnings=True, errors=True):
        self.warnings = warnings
        self.errors = errors

    @classmethod
    def from_config_file(cls):
        config_parser = ConfigInitializer.get_config_parser()
        warnings = config_parser.getboolean('logging', 'warnings')
        errors = config_parser.getboolean('logging', 'errors')
        return cls(warnings, errors)

    def print_info(self, message):
        info_prefix = '\n[INFO]    '
        print(info_prefix + message)

    def print_done(self, message):
        done_prefix = '\n[' + colored('DONE', 'green') + ']    '
        print(done_prefix + message)

    def print_warning(self, message):
        if self.warnings:
            warn_prefix = '\n[' + colored('WARN', 'yellow') + ']    '
            print(warn_prefix + message)

    def print_error(self, message):
        if self.errors:
            error_prefix = '\n[' + colored('ERROR', 'red') + ']   '
            print(error_prefix + message)
