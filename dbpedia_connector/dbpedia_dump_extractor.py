import re
from random import randint


class DBpediaDumpExtractor(object):
    def __init__(self, ttl_path='../data/mappingbased_objects_en.ttl', randomize=False):
        self.ttl_path = ttl_path
        self.randomize = randomize

    def yield_entries(self):
        if self.randomize:
            offset_countdown = randint(0, 10000)  # TODO: get rid off magic number
        else:
            offset_countdown = 0

        with open(self.ttl_path, 'rb') as fin:
            for line in fin:
                if offset_countdown > 0:
                    offset_countdown -= 1
                    continue

                items = re.findall(r'<([^>]+)>', line)
                if len(items) == 0:
                    continue
                assert len(items) == 3  # otherwise this type of .ttl is not supported by this method
                subject, predicate, object = items
                yield subject, predicate, object
