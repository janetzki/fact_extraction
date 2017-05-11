from termcolor import colored
from config_initializer.config_initializer import ConfigInitializer


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

    def print_aligned(self, message):
        alignment = ' ' * 10
        print(alignment + message)

    def print_info(self, message):
        info_prefix = '\n[info]    '
        print(info_prefix + message)

    def print_done(self, message):
        done_prefix = '\n[' + colored('done', 'green') + ']    '
        print(done_prefix + message)

    def print_warning(self, message):
        if self.warnings:
            warn_prefix = '\n[' + colored('warn', 'yellow') + ']    '
            print(warn_prefix + message)

    def print_error(self, message):
        if self.errors:
            error_prefix = '\n[' + colored('error', 'red') + ']   '
            print(error_prefix + message)

    def print_pass(self, message):
        pass_prefix = '\n[' + colored('passed', 'green') + ']  '
        print(pass_prefix + message)

    def print_fail(self, message):
        fail_prefix = '\n[' + colored('failed', 'red') + ']  '
        print(fail_prefix + message)
