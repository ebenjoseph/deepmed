"""Functions for working with cochrane data, specifically their paper reviews.
"""
import re


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
	'Low risk': 1,
	'Unclear risk': 0,
	'High risk': -1,
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
PATIENT_ACCOUNT = 'patient-account'
HEADER_MATCHERS = _create_matchers({
	'Blinding': BLINDING,
	'Random sequence generation': RANDOMIZATION,
	'Outcome data': PATIENT_ACCOUNT,
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
	blinding_scores = []
	randomization_scores = []
	patient_account_scores = []
	print headers
	for header, (rating, _) in headers.iteritems():
		normalized_header = _normalize_header(header)
		normalized_rating = _normalize_rating(rating)
		if normalized_header == 'blinding':
			blinding_scores.append(normalized_rating)
		elif normalized_header == 'randomization':
			randomization_scores.append(normalized_rating)
	return {
		'blinding.mentioned': 1 if blinding_scores else 0,
		'blinding.appropriate': sum(blinding_scores),
		'randomization.mentioned': 1 if randomization_scores else 0,
		'randomization.appropriate': sum(randomization_scores),
		'patient-account': sum(patient_account_scores)
	}


def jadadify(data):
	"""Return a Jadad review mapping category to score."""
	return _normalize_headers(data['table'])


def score(data):
	"""Return a Jadad score as a scalar number."""
	return sum(jadadify(data).values())
