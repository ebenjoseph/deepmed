"""Because the ``statistics`` model is a POS, this ``stats`` module provides
basic statistical functions.
"""

import math


def mean(values):
	"""Average value: sum / length."""
	return float(sum(values)) / len(values)


def stdev(values):
	"""The standard deviation ``values``; assumes the values are evenly
	distributed.
	"""
	return math.sqrt(1.0 / (len(values) - 1) *
					 sum((v - mean(values)) ** 2 for v in values))
