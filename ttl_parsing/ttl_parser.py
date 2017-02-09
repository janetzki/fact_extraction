import re
import imp
import io
from random import randint

logger = imp.load_source('logger', '../logging/logger.py')
from logger import Logger

line_counting = imp.load_source('line_counting', '../helper_functions/line_counting.py')
uri_rewriting = imp.load_source('uri_rewriting', '../helper_functions/uri_rewriting.py')


class TTLParser(object):
    def __init__(self, ttl_path, randomize=False):
        self.ttl_path = ttl_path
        self.randomize = randomize
        self.logger = Logger.from_config_file()

    def yield_cleaned_entry_names(self):
        for subject, predicate, object in self.yield_entries():
            subject = uri_rewriting.strip_cleaned_name(subject)
            predicate = uri_rewriting.strip_cleaned_name(predicate)
            object = uri_rewriting.strip_cleaned_name(object)
            yield subject, predicate, object

    def yield_entries(self):
        if self.randomize:
            total_lines = line_counting.cached_counter.count_lines(self.ttl_path)
            offset_countdown = randint(0, total_lines / 2)  # start in the first half to provide enough results
        else:
            offset_countdown = 0

        with io.open(self.ttl_path, encoding='utf-8') as fin:
            for line in fin:
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
