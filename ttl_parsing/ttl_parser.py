import re
import imp
from random import randint

line_counting = imp.load_source('line_counting', '../helper_functions/line_counting.py')
uri_rewriting = imp.load_source('uri_rewriting', '../helper_functions/uri_rewriting.py')


class TTLParser(object):
    def __init__(self, ttl_path, randomize=False):
        self.ttl_path = ttl_path
        self.randomize = randomize

    def yield_cleaned_entry_names(self):
        for subject, predicate, object in self.yield_entries():
            subject = uri_rewriting.strip_cleaned_name(subject)
            predicate = uri_rewriting.strip_cleaned_name(predicate)
            object = uri_rewriting.strip_cleaned_name(object)
            yield subject, predicate, object

    def yield_entries(self):
        for subject, predicate, object, length in self.yield_entries_and_length():
            yield subject, predicate, object

    def yield_entries_and_length(self):
        if self.randomize:
            total_lines = line_counting.cached_counter.count_lines(self.ttl_path)
            offset_countdown = randint(0, total_lines / 2)  # start in the first half to provide enough results
        else:
            offset_countdown = 0

        with open(self.ttl_path, 'rb') as fin:
            for line in fin:
                if offset_countdown > 0:
                    offset_countdown -= 1
                    continue

                # TODO: discard double underscores
                items = re.findall(r'<([^>]+)>', line)
                if not len(items) == 3:
                    continue
                # assert len(items) == 3  # otherwise this type of .ttl is not supported by this method
                subject, predicate, object = items
                length = len(line)
                yield subject, predicate, object, length  # length is for character index creation
