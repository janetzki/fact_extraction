from logger import Logger
import pickle
import os

dir_path = os.path.dirname(os.path.abspath(__file__)) + '/'


class LineCounter(object):
    """
    Count lines of files and cache the results.
    """

    def __init__(self, line_numbers_path=dir_path + "../data/line_numbers.pkl"):
        """
        Specify where to save the cached line counts.

        :param line_numbers_path: input and output file for cached line counts
        """
        self.line_numbers_path = line_numbers_path
        self.logger = Logger.from_config_file()

        if os.path.exists(self.line_numbers_path):
            with open(self.line_numbers_path) as fin:
                self.line_numbers = pickle.load(fin)
        else:
            self.line_numbers = {}

    @staticmethod
    def _make_gen(reader):
        """
        Yield data chunks from a file.
        http://stackoverflow.com/questions/19001402/how-to-count-the-total-number-of-lines-in-a-text-file-using-python

        :param reader: handle to a file
        :yield: data chunks
        """
        b = reader(1024 * 1024)
        while b:
            yield b
            b = reader(1024 * 1024)

    @staticmethod
    def _count_lines(path):
        """
        Count the lines of a file.
        http://stackoverflow.com/questions/19001402/how-to-count-the-total-number-of-lines-in-a-text-file-using-python

        :param path: input file
        :return: number of lines
        """
        print('Counting lines of file: "' + path + '" ...')
        fin = open(path, 'rb')
        f_gen = LineCounter._make_gen(fin.read)
        lines = sum(buf.count(b'\n') for buf in f_gen)
        print(str(lines) + ' lines')
        return lines

    def count_lines(self, path):
        """
        Count the lines of a file if and store the result in the cache. The file is considered to have changed if its
        size has changed. The cache is then updated.

        :param path: input file
        :return: number of lines
        """
        file_size = os.path.getsize(path)

        if path in self.line_numbers:
            if file_size == self.line_numbers[path]['size']:
                self.logger.print_info(str(self.line_numbers[path]['line_count']) + ' lines (cached)')
                return self.line_numbers[path]['line_count']

        self.line_numbers[path] = {}
        self.line_numbers[path]['line_count'] = LineCounter._count_lines(path)
        self.line_numbers[path]['size'] = file_size

        with open(self.line_numbers_path, 'wb+') as fout:
            pickle.dump(self.line_numbers, fout)

        return self.line_numbers[path]['line_count']


# Singleton for a single cache
cached_counter = LineCounter()
