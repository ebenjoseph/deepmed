from xml.dom import minidom
import json
import os
import sys
import argparse


outfile = open('cochrane_refs.jsonl', 'a')

for f in sys.stdin:
	filename = f[:-2]
	doc_id = filename.split(' ')[0]
	xmldoc = minidom.parse(filename)
	studies = xmldoc.getElementsByTagName('STUDY')

	for s in studies:
		if 'include' in s.parentNode.tagName.lower():
			data = {}
			data['id'] = doc_id+'-'+s.attributes['ID'].value
			n = 0
			ref = s.childNodes[1]
			for c in ref.childNodes:
				if n % 2 > 0:
					try:
						data[ref.childNodes[n].tagName] = ref.childNodes[n].firstChild.nodeValue
					except:
						break
				n += 1
			json.dump(data, outfile)
			outfile.write('\n')




'''
# get all studies
studies = xmldoc.getElementsByTagName('STUDY')
# check parent node is INCLUDED_STUDIES
studies[0].parentNode.tagName
# get cochrane study ID
studies[0].attributes['ID'].value
# get name of reference node
studies[0].childNodes[1].tagName
# get TI value
studies[0].childNodes[1].childNodes[3].firstChild.nodeValue
'''

