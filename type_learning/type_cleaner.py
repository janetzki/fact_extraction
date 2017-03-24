import imp
from tqdm import tqdm

type_tool = imp.load_source('type_tool', '../storing_tools/type_tool.py')
from type_tool import TypeTool


class TypeCleaner(TypeTool):
    def __init__(self, input_path='../data/type_patterns_raw.pkl',
                 output_path='../data/type_patterns_cleaned.pkl',
                 subject_minimum=0, object_minimum=0):
        super(TypeCleaner, self).__init__(input_path, output_path)
        self.subject_minimum = subject_minimum
        self.object_minimum = object_minimum

    @classmethod
    def from_config_file(cls):
        config_parser = cls.get_config_parser()
        section = 'type_learner'
        subject_minimum = config_parser.getfloat(section, 'subject_minimum')
        object_minimum = config_parser.getfloat(section, 'object_minimum')
        return cls(subject_minimum=subject_minimum, object_minimum=object_minimum)



    def calculcate_probabilities(self, type_pattern, key_attr):
        types = getattr(type_pattern, key_attr + "_types")
        probabilities = getattr(type_pattern, key_attr + "_probabilities")
        total = sum(types.values())
        weighted_probabability = 0
        for type, quantity in types.iteritems():
            type_frequency = float(quantity) / type_pattern.facts
            all_frequencies = 0
            for predicate in self.type_patterns:
                another_type_pattern = self.type_patterns[predicate]
                other_types = getattr(another_type_pattern, key_attr + "_types")
                if type in other_types:
                    all_frequencies += float(other_types[type]) / another_type_pattern.facts

            #print type, type_frequency, all_frequencies
            probability = type_frequency / all_frequencies
            probabilities[type] = probability
            weighted_probabability += float(quantity) / total * probability

        return weighted_probabability


    def clean_types(self):
        self.logger.print_info('Type cleaning...')

        for predicate in self.type_patterns:
            self.type_patterns[predicate].clean_subject_types(self.subject_minimum)
            self.type_patterns[predicate].clean_object_types(self.object_minimum)


        self.logger.print_info('Calculate probabilities for each pattern...')
        for predicate in tqdm(self.type_patterns, total=len(self.type_patterns)):
            type_pattern = self.type_patterns[predicate]
            type_pattern.subject_weighted_probability = self.calculcate_probabilities(type_pattern, "subject")
            type_pattern.object_weighted_probability = self.calculcate_probabilities(type_pattern, "object")

        print self.type_patterns
        self.logger.print_done('Type cleaning completed.')


if __name__ == '__main__':
    pattern_cleaner = TypeCleaner.from_config_file()
    pattern_cleaner.clean_types()
    pattern_cleaner.save()
