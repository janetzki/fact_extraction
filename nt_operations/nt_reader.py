import re
import imp
import io
from random import randint
from tqdm import tqdm

logger = imp.load_source('logger', '../logging/logger.py')
from logger import Logger

line_counting = imp.load_source('line_counting', '../helper_functions/line_counting.py')
uri_rewriting = imp.load_source('uri_rewriting', '../helper_functions/uri_rewriting.py')


class NTReader(object):
    def __init__(self, nt_path, randomize=False):
        self.nt_path = nt_path
        self.randomize = randomize
        self.logger = Logger.from_config_file()

    def yield_cleaned_entry_names(self):
        for subject, predicate, object in self.yield_entries():
            subject = uri_rewriting.strip_cleaned_name(subject)
            predicate = uri_rewriting.strip_cleaned_name(predicate)
            object = uri_rewriting.strip_cleaned_name(object)
            yield subject, predicate, object

    def yield_entries(self):
        total_lines = line_counting.cached_counter.count_lines(self.nt_path)
        if self.randomize:
            offset_countdown = randint(0, total_lines / 2)  # start in the first half to provide enough results
        else:
            offset_countdown = 0

        self.logger.print_info('Reading facts from "' + self.nt_path + '"...')
        with io.open(self.nt_path, encoding='utf-8') as fin:
            for line in tqdm(fin, total=total_lines):
                if offset_countdown > 0:
                    offset_countdown -= 1
                    continue

                items = re.findall(r'<([^>]+)>', line)
                if not len(items) == 3:
                    self.logger.print_warning('Bad .ttl line: ' + line)
                    continue
                subject, predicate, object = items
                if '__' in subject:
                    continue  # those entities are not part of Wikipedia
                yield subject, predicate, object
