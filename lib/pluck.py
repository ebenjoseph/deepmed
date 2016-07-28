import json

CONTENT_WORDS = [
	'Abstract',
	'Method',
	'Summary',
	'Result',
	'Conclusion',
	'Discussion',
	'Material',
	'Future',
]


def find_indices(string, keyword):
	"""Yields the indices ``keywords`` within string."""
	index = -1
	while True:
		try:
			index = string.index(keyword, index + 1)
		except ValueError:
			break
		else:
			yield index


def get_surround(string, keyword, before=100, after=100):
	"""Yields the keyword with the surrounding text"""
	for index in find_indices(string, keyword):
		start = max(0, index - before)
		end = min(len(string), index + after)
		yield string[start:end]


def text_content(data, content_words=None):
	"""Pluck the text content from the entry data. A content section has a title
	containing a ``content_word``.
	"""
	content_words = content_words or CONTENT_WORDS
	content_string = ''
	for key in data['content']:
		for word in content_words:
			if key.lower().find(word.lower()) >= 0:
				content_string += data['content'][key]
				content_string += ' '
	return content_string


def jsonl(filename):
	"""Read ``jsonl`` file yielding each parsed line."""
	with open(filename, 'r') as file_:
		for line in file_:
			yield json.loads(line)
