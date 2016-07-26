"""
The ``readability`` module contains extractors for a text's "ease of reading", i.e.
some ratios between syllables and words.
"""
from collections import OrderedDict
import math

from nltk.corpus import cmudict
from nltk.tokenize import sent_tokenize, word_tokenize

CMUDICT = cmudict.dict()
EXTRACTORS = OrderedDict()


def stdev(values):
	mean = float(sum(values)) / len(values)
	return math.sqrt(1.0 / (len(values) - 1) * sum((v - mean) ** 2 for v in values))


def syllables(word):
	lower = word.lower()
	if lower in CMUDICT:
		return [len(list(y for y in x if y[-1].isdigit())) for x in CMUDICT[lower]]


def extractor(name):
	def wrapper(extractor):
		EXTRACTORS[name] = extractor
		return extractor
	return wrapper


def _get_hardwords(words, **kwargs):
	return [word for word, syllables in words if syllables and syllables[0] > 2]


@extractor('characters')
def char_count(string, **kwargs):
	return len(string)

@extractor('words')
def word_count(words, **kwargs):
	return len(words)

@extractor('sentences')
def sentence_count(sentences, **kwargs):
	return len(sentences)

@extractor('chars-per-word-mean')
def word_length_avg(string, words, **kwargs):
	word_lengths = [len(word) for word, _ in words]
	return float(sum(word_lengths)) / len(words)

@extractor('chars-per-word-stdev')
def word_length_stdev(words, **kwargs):
	word_lengths = [len(word) for word, _ in words]
	return stdev(word_lengths)

@extractor('words-per-sentence-mean')
def sentence_length_avg(words, sentences, **kwargs):
	return float(len(words)) / len(sentences)

@extractor('words-per-sentence-stdev')
def sentence_length_std(sentences, **kwargs):
	sentence_lengths = list(len(word_tokenize(sentence)) for sentence in sentences)
	return stdev(sentence_lengths)

@extractor('syallables-per-word-mean')
def syllables_per_word_mean(words, **kwargs):
	syllables = [word_syllables[0] for _, word_syllables in words if word_syllables]
	return float(sum(syllables)) / len(words)

@extractor('syallables-per-word-stdev')
def syllables_per_word_stdev(words, **kwargs):
	syllables = [word_syllables[0] for _, word_syllables in words if word_syllables]
	return stdev(syllables)

@extractor('ARI')
def automated_readability_index(string, words, sentences):
	return 4.71 * (len(string) / len(words)) + 0.5 * (len(words) / len(sentences)) - 21.43

@extractor('hard-word-ratio')
def hardword_count(words, **kwargs):
	return float(len(_get_hardwords(words))) / len(words)

@extractor('lexical-density')
def lexical_density(words, **kwargs):
	return float(len(set([word for word, syllable in words]))) / len(words)

@extractor('gunning-fog-index')
def general_fog_index(**kwargs):
	return 0.4 * (sentence_length_avg(**kwargs) + hardword_count(**kwargs))

@extractor('coleman-liau-index')
def coleman_liau_index(**kwargs):
	return 5.88 * word_length_avg(**kwargs) + 20.96 * (1 / sentence_length_avg(**kwargs)) - 15.8

@extractor('SMOG')
def smog_index(**kwargs):
	hardwords = _get_hardwords(**kwargs)
	return 1.043 * math.sqrt(len(hardwords) * (30 / float(sentence_count(**kwargs)))) + 3.1291

@extractor('flesch-kincaid-index')
def flesch_kincaid_index(**kwargs):
	return 206.835 - 1.015 * sentence_length_avg(**kwargs) - 84.6 * syllables_per_word_mean(**kwargs)

def extract(string):
	words = word_tokenize(string)
	sentences = sent_tokenize(string)
	kwargs = {
		'string': string,
		'words': [(word, syllables(word)) for word in words],
		'sentences': sentences,
	}
	return OrderedDict((name, function(**kwargs)) for name, function in EXTRACTORS.iteritems())

def extractors():
	"""Return the list of extractor names."""
	return EXTRACTORS.keys()
