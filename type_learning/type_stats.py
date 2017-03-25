import imp
from tqdm import tqdm

type_tool = imp.load_source('type_tool', '../storing_tools/type_tool.py')
from type_tool import TypeTool


class TypeStatistician(TypeTool):
    def __init__(self, input_path='../data/type_patterns_cleaned.pkl'):
        super(TypeStatistician, self).__init__(input_path)

    @classmethod
    def from_config_file(cls):
        config_parser = cls.get_config_parser()
        section = 'type_learner'
        return cls()

    def print_stats(self):
        scores = dict()
        print ';'.join(["relation", "facts", "subject", "best subject type", "best subject type score",
                        "object", "best object type", "best object type score", "arithmetic mean"])
        for predicate in self.type_patterns:
            pattern = self.type_patterns[predicate]
            max_subject_type_score = 0
            max_subject_type = ""
            max_object_type_score = 0
            max_object_type = ""
            for type in pattern.subject_probabilities:
                if max_subject_type_score < pattern.subject_probabilities[type]:
                    max_subject_type = type.decode('utf-8')
                    max_subject_type_score = pattern.subject_probabilities[type]
            for type in pattern.object_probabilities:
                if max_object_type_score < pattern.object_probabilities[type]:
                    max_object_type = type.decode('utf-8')
                    max_object_type_score = pattern.object_probabilities[type]

            arithmetic_mean = (pattern.subject_weighted_probability + pattern.object_weighted_probability) / 2
            print ";".join([predicate, str(pattern.facts), str(pattern.subject_weighted_probability), max_subject_type,
                            str(max_subject_type_score), str(pattern.object_weighted_probability), max_object_type,
                            str(max_object_type_score), str(arithmetic_mean)])

if __name__ == '__main__':
    stats = TypeStatistician.from_config_file()
    stats.print_stats()
