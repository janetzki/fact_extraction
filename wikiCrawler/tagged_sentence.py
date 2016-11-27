class TaggedSentence(object):
    def __init__(self, sentence, tags):
        self.sentence = sentence
        self.tags = tags

    @classmethod
    def fromHtml(html):
        return TaggedSentence(sentence, tags)