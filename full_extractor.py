# pubtype extractor

import json
import csv
from lib import readability

contentWords = ['Abstract', 'Method', 'Summary', 'Result', 'Conclusion', 'Discussion', 'Material', 'Future']

words = [
"Doc ID",
"Clinical Trial",
"Multicenter Study",
"Comparative Study",
"Randomized Controlled Trial",
"Non-U.S. Gov't",
"N.I.H., Extramural",
"Letter",
"Non-P.H.S.",
"Pragmatic Clinical Trial",
"Observational Study",
"Phase I",
"Phase II",
"Phase III",
"Phase IV",
"pval-1",
"pval-2",
"pval-3",
"pval-4",
"pval-5",
"n-1",
"n-2",
"n-3",
"n-4",
"n-5",
"funding-1",
"funding-2",
"funding-3",
"funding-4",
"funding-5",
"sections",
] + readability.extractors()

out = open('../finalout.csv', 'w')
a = csv.writer(out)

CUTOFF = 5
a.writerow(words)

pubDocs = {}
artDocs = {}

with open('../modeling/Arduino_ES_output_filtered.jsonl') as f:
	for line in f:
		pval = open('../csv_outputs/pval_output.csv', 'r')
		n = open('../csv_outputs/n_output.csv', 'r')
		funding = open('../csv_outputs/funding_output.csv', 'r')

		data = json.loads(line)
		#docData = {}
		info = []

		#docData['id'] = data['id']
		pubInfo = data['pubtypes'].lower()
		content = data['content']

		info.append(data['pmid'])

		# extract pubtypes info
		for word in words[1:15]:
			if pubInfo.find(word.lower()) >= 0:
				info.append(1)
			else:
				info.append(0)

		c = 0
		existing = []
		for line in pval:
			row = line.split(',')
			if int(row[0]) == int(data['pmid']):
				if row[2].strip() not in existing:
					existing.append(row[2].strip())  # add to array if not there yet
					c += 1
			if c == CUTOFF: 
				print 'more than 5 pvals'
				break

		while c < CUTOFF:
			existing.append(0)
			c += 1

		for i in existing:
			info.append(i)

		c = 0
		for line in n:
			row = line.split(',')
			if int(row[0]) == int(data['pmid']):
				num = row[2].strip().lower()
				try:
					if int(num) not in info:
						info.append(int(num))
						c += 1
				except:
					try:
						num = text2int(num)
						if num not in info:
							info.append(text2int(num))
							c += 1
					except:
						print ''
				#c += 1
			if c == CUTOFF: 
				print 'more than 5 n'
				break

		while c < CUTOFF:
			info.append(0)
			c += 1

		c = 0
		existing = []
		for line in funding:
			row = line.split(',')
			if int(row[0]) == int(data['pmid']):
				if row[2].strip() not in existing:
					existing.append(row[2].strip())
					c += 1
			if c == CUTOFF: 
				print 'more than 5 funding agencies'
				break

		while c < CUTOFF:
			existing.append(0)
			c += 1

		for i in existing:
			info.append(i)


		# num sections
		info.append(len(content.keys()))


		# extract readability data
		contentString = ""

		# content extractor
		for key in content:
			for word in contentWords:
				if key.lower().find(word.lower()) >= 0:
					contentString += data['content'][key]
					contentString += ' '

		if len(contentString) < 1000: continue

		readability_dict = readability.extract(contentString)
		info += readability_dict.values()


		a.writerow(info)

		pval.close()
		n.close()
		funding.close()


def text2int(textnum, numwords={}):
	if not numwords:
		units = [
		"zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]

		tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

		scales = ["hundred", "thousand", "million", "billion", "trillion"]

		numwords["and"] = (1, 0)
		for idx, word in enumerate(units):    numwords[word] = (1, idx)
		for idx, word in enumerate(tens):     numwords[word] = (1, idx * 10)
		for idx, word in enumerate(scales):   numwords[word] = (10 ** (idx * 3 or 2), 0)

	current = result = 0
	for word in textnum.split(" "):
		if word not in numwords:
			raise Exception("Illegal word: " + word)

		scale, increment = numwords[word]
		current = current * scale + increment
		if scale > 100:
			result += current
			current = 0

	return result + current
