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


@extractor('words')
def word_count(words, **kwargs):
    return len(words)

@extractor('ARI')
def automated_readability_index(string, words, sentences):
    return 4.71 * (len(string) / len(words)) + 0.5 * (len(words) / len(sentences)) - 21.43

@extractor('hard-words')
def hardword_count(words, **kwargs):
    hardwords = [word for word, syllables in words if syllables and syllables[0] > 2]
    return float(len(hardwords)) / len(words)

@extractor('lexical-density')
def lexical_density(words, **kwargs):
    return float(len(set([word for word, syllable in words]))) / len(words)

@extractor('sentences')
def sentence_count(sentences, **kwargs):
    return len(sentences)



def extract(string):
    words = word_tokenize(string)
    sentences = sent_tokenize(string)
    kwargs = {
        'string': string,
        'words': [(word, syllables(word)) for word in words],
        'sentences': sentences,
    }
    return {name: function(**kwargs) for name, function in EXTRACTORS.iteritems()}
