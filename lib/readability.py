"""
The ``readability`` module contains extractors for a text's "ease of reading", i.e.
some ratios between syllables and words.
"""

from nltk.corpus import cmudict
from nltk.tokenize import sent_tokenize, word_tokenize

CMUDICT = cmudict.dict()
EXTRACTORS = {}


def syllables(word):
    lower = word.lower()
    if lower in CMUDICT:
        return [len(list(y for y in x if y[-1].isdigit())) for x in CMUDICT[lower]]


def extractor(name):
    def wrapper(extractor):
        EXTRACTORS[name] = extractor
        return extractor
    return wrapper


@extractor('characters')
def char_count(string, **kwargs):
    return len(string)


@extractor('word')
def word_count(words, **kwargs):
    return len(words)


def extract(string):
    words = word_tokenize(string)
    sentences = sent_tokenize(string)
    kwargs = {
        'string': string,
        'words': [(word, syllables(word)) for word in words],
        'sentences': sentences,
    }
    return {name: function(**kwargs) for name, function in EXTRACTORS.iteritems()}
