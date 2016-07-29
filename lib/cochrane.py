"""Functions for working with cochrane data, specifically their paper reviews.
"""
from collections import defaultdict
import re

from . import stats

def _create_matchers(matchers, flags=re.IGNORECASE):
	return {re.compile(regex, flags): value
			for regex, value in matchers.iteritems()}


def _match(string, matchers):
	"""A ``matcher`` is a dictionary mapping a regex to a value."""
	for matcher, value in matchers.iteritems():
		if next(matcher.finditer(string), None):
			return value
	raise ValueError('could not find match for {}'.format(string))


RATING_MATCHERS = _create_matchers({
	'Low': 1,
	'Unclear': 0,
	'High': -1,
})


# Jadad Score:
# - (2) blinding
#   - ( 1) mentioned
#   - ( 1) appropriate
#   - (-1) inappropriate
# - (2) randomization
#   - ( 1) mentioned
#   - ( 1) appropriate
#   - (-1) inappropriate
# - (1) patients-accounted
BLINDING = 'blinding'
RANDOMIZATION = 'randomization'
PATIENTS_ACCOUNTED = 'patients-accounted'
HEADER_MATCHERS = _create_matchers({
	'blinding': BLINDING,
	'sequence generation': RANDOMIZATION,
	'allocation concealment': RANDOMIZATION,
	'selective reporting': PATIENTS_ACCOUNTED,
	'incomplete outcome data': PATIENTS_ACCOUNTED,
})


def _normalize_rating(rating, matchers=None):
	"""Returns the ``rating`` string normalized as an integer value.

	If ``matchers`` dosn't have any matches an exception is raised. Note
	that the first match is returned.
	"""
	matchers = matchers or RATING_MATCHERS
	return _match(rating, matchers)


def _normalize_header(header, matchers=None):
	matchers = matchers or HEADER_MATCHERS
	try:
		return _match(header, matchers)
	except ValueError:
		return None


def _normalize_headers(headers):
	"""To normalize the cochrane paper reviews we collect and categorize
	each review assessment. If it correlates with a Jadad score the assessment
	is collected an normalized. All assessment scores are averaged to get the
	corresponding ``appropriate`` Jadad score. The ``mentioned`` Jadad score
	is set to whether an assessment for the relevant category is present.
	"""
	scores = defaultdict(lambda: list())
	def mean(key):
		return stats.mean(scores[key]) if scores[key] else 0
	for header, (rating, _) in headers.iteritems():
		normalized_header = _normalize_header(header)
		if normalized_header:
			normalized_rating = _normalize_rating(rating)
			# Patient
			if normalized_header is PATIENTS_ACCOUNTED and normalized_rating == -1:
				scores[normalized_header].append(0)
			elif normalized_rating is not 0:
				scores[normalized_header].append(normalized_rating)
	if any(scores.values()):
		return {
			'blinding.mentioned': 1.0 if any(scores[BLINDING]) else 0,
			'blinding.appropriate': mean(BLINDING),
			'randomization.mentioned': 1.0 if any(scores[RANDOMIZATION]) else 0,
			'randomization.appropriate': mean(RANDOMIZATION),
			'patient-account': mean(PATIENTS_ACCOUNTED),
		}
	else:
		raise ValueError('no review data extracted')


def _pubmed_url_to_id(url):
	splits = url.rsplit('/', 1)
	if len(splits) != 2:
			raise ValueError('improper pubmed url: {}'.format(url))
	return splits[-1]


# Public Interface

def jadad_scores(data):
	"""Return a Jadad review mapping category to score."""
	return _normalize_headers(data['table'])


def jadad_score(data):
	"""Return a Jadad score as a scalar number."""
	return reduce_jadad_scores(jadad_scores(data))


def reduce_jadad_scores(scores):
	"""Return the overall score for ``scores``."""
	return sum(scores.values())


def pubmed_id(data):
	return _pubmed_url_to_id(data['pubmedurl'])
