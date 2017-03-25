from collections import Counter


class TypePattern(object):
    def __init__(self):
        self.facts = 0
        self.subject_types = Counter()
        self.subject_probabilities = dict()
        self.subject_weighted_probability = 0
        self.object_types = Counter()
        self.object_probabilities = dict()
        self.object_weighted_probability = 0

    def __repr__(self):
        return "Subject: " + str(self.subject_types) + str(self.subject_probabilities) + \
               "Subject weighted: " + str(self.subject_weighted_probability) + \
               "Object: " + str(self.object_types) + str(self.object_probabilities) + \
               "Object weighted: " + str(self.object_weighted_probability)

    def clean_types(self, types, minimum):
        if 0 < minimum < 1:
            minimum = self.facts * minimum

        new_types = Counter()
        for type, quantity in types.iteritems():
            if quantity >= minimum:
                new_types[type] += quantity
        return new_types

    def clean_subject_types(self, minimum):
        self.subject_types = self.clean_types(self.subject_types, minimum)

    def clean_object_types(self, minimum):
        self.object_types = self.clean_types(self.object_types, minimum)
