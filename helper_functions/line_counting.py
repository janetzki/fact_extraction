import pickle
import os.path
import imp

logger = imp.load_source('logger', '../logging/logger.py')
from logger import Logger


class LineCounter(object):
    def __init__(self, line_numbers_path="../data/line_numbers.pkl"):
        self.line_numbers_path = line_numbers_path
        self.logger = Logger.from_config_file()

        if os.path.exists(self.line_numbers_path):
            with open(self.line_numbers_path) as fin:
                self.line_numbers = pickle.load(fin)
        else:
            self.line_numbers = {}

    def count_lines(self, path):
        file_size = os.path.getsize(path)

        if path in self.line_numbers:
            if file_size == self.line_numbers[path]['size']:
                self.logger.print_info(str(self.line_numbers[path]['line_count']) + ' lines (cached)')
                return self.line_numbers[path]['line_count']

        self.line_numbers[path] = {}
        self.line_numbers[path]['line_count'] = count_lines(path)
        self.line_numbers[path]['size'] = file_size

        with open(self.line_numbers_path, 'wb+') as fout:
            pickle.dump(self.line_numbers, fout)

        return self.line_numbers[path]['line_count']


cached_counter = LineCounter()


def _make_gen(reader):
    # http://stackoverflow.com/questions/19001402/how-to-count-the-total-number-of-lines-in-a-text-file-using-python
    b = reader(1024 * 1024)
    while b:
        yield b
        b = reader(1024 * 1024)


def count_lines(path):
    # http://stackoverflow.com/questions/19001402/how-to-count-the-total-number-of-lines-in-a-text-file-using-python
    print('Counting lines of file: "' + path + '" ...')
    file = open(path, 'rb')
    f_gen = _make_gen(file.read)
    lines = sum(buf.count(b'\n') for buf in f_gen)
    print(str(lines) + ' lines')
    return lines
