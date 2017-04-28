from tqdm import tqdm
import codecs
import imp

logger = imp.load_source('logger', '../logging/logger.py')
from logger import Logger


class NTWriter(object):
    def __init__(self, nt_path):
        self.nt_path = nt_path
        self.logger = Logger.from_config_file()

    def write_nt(self, n_triples):
        with codecs.open(self.nt_path, 'wb', 'utf-8') as fout:
            self.logger.print_info('\n\nSaving facts to "' + self.nt_path + '"...')
            for subject, predicate, object in tqdm(n_triples):
                fout.write('<' + subject + '> <' + predicate + '> <' + object + '> .\n')
