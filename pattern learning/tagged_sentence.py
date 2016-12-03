class TaggedSentence(object):
    def __init__(self, sentence, absolute_position, article_length=-1):
        self.sentence = sentence  # provisional - TODO: replace with token and tag list
        self.absolute_position = absolute_position  # zero based counting
        self.article_length = article_length  # number of sentences

    def set_article_length(self, article_length):
        self.article_length = article_length

    def calculate_relative_position(self):
        return self.absolute_position / float(self.article_length)

    def as_string(self):
        return self.sentence
