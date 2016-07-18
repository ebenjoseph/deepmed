import json

setKeys = ['pmid', 'golden']
contentWords = ['result', 'summary', 'abstract']
finalContent = []
tables = [0, 1]

outfile = open('ES_pval1000.jsonl', 'a')

with open('Arduino_ES_output1000.jsonl') as file:
	for line in file:
		data = json.loads(line)
		finalData = {}

		# get baseline data for DD
		finalData['id'] = data['pmid']
		finalData['golden'] = data['golden']
		finalData['link'] = data['link']
		finalData['pubtypes'] = data['pubtypes']
		finalData['title'] = data['title']

		contentString = ""

		# content extractor
		for key in data['content']:
			for word in contentWords:
				#print key, word
				if key.lower().find(word.lower()) >= 0:
					#print data['content'][key]
					contentString += data['content'][key]
					contentString += ' '

		finalData['content'] = contentString

		# table extractor
		'''
		for table in data['content']['Tables']:
			for word in contentWords:
				if table['Section'].lower().find(word.lower()) >= 0:
		'''

		if len(contentString) > 0 and len(contentString) < 100: continue


		json.dump(finalData, outfile)
		outfile.write('\n')