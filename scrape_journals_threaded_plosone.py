# comment

import requests
import sys
from time import sleep
from bs4 import BeautifulSoup
import re
import logging
from datetime import datetime
import csv
import json
import re
import xml.etree.ElementTree
from multiprocessing.dummy import Pool as ThreadPool
import threading

journals_to_scrape = []
outfile = open('output_test.jsonl', 'a')

# read in csv
with open('testing.csv', 'rU') as csvfile:
	reader = csv.reader(csvfile, delimiter=',')
	counter = 0
	for row in reader:
		data = {}
		if not counter:
			counter += 1
			continue

		data['journal'] = row[6]
		data['id'] = row[16]
		data['link'] = row[13]
		journals_to_scrape.append(data)


'''links_to_scrape = [
'http://dx.doi.org/10.1111/j.1532-5415.2011.03391.x',
'http://linkinghub.elsevier.com/retrieve/pii/S0735-1097(04)01219-7',
'http://www.ima.org.il/IMAJ/ViewArticle.aspx?year=2010&month=08&page=489'
]'''

counter = 0
docs = []
p = re.compile(ur'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', re.MULTILINE)
sub = u"\n\n"
journalsRead = {}

# read in previously read journal links
journalfile = open('journals', 'r')
for line in journalfile:
	journalsRead[line.rstrip()] = 1

journalfile.close()
journalfile = open('journals', 'a')

journalLock = threading.Lock()
writingLock = threading.Lock()

# setup logging
logging.basicConfig(filename='scraping_log.log',level=logging.DEBUG)
logging.info("Scraper started " + str(datetime.now()) )

def getsoup(root_link):
	try:
		web_page = requests.get(root_link)
	except:
		logging.info('error parsing initial page')
		return -1
	sleep(2)
	return BeautifulSoup(web_page.content, "html.parser")

def remove_tags(text):
  return ''.join(xml.etree.ElementTree.fromstring(text).itertext())

def pull_journal(journal):
	root_link = journal['link']

	#if not len(journalsRead) % 10: print len(journalsRead)
	
	journalLock.acquire()

	print len(journalsRead)

	try:
		journalsRead[root_link]
		journalLock.release()
		print 'skipping'
		return
	except:
		journalsRead[root_link] = 1

	journalfile.write(root_link)
	journalfile.write('\n')

	journalLock.release()
	
	data = {}
	fullarticle = ""

	try:
		if root_link.find('cid.oxfordjournals.org') > 0:
			data['journal'] = journal['journal']
			soup = getsoup(root_link)
			fullarticle = str(soup.find('div', itemprop='articleBody'))

		# final catch-all attempt
		else:
			try:
				data['journal'] = journal['journal']
				soup = getsoup(root_link)
				fullarticle = str(soup.find('div', itemprop='articleBody'))
			except:
				return


		try:
			clean = remove_tags(fullarticle)
			clean = ' '.join(clean.split())
		except:
			clean = re.sub('<[^<]+?>', '', fullarticle.decode('utf-8'))  #fullarticle.decode('utf-8')
			clean = ' '.join(clean.split())

		# if fullarticle length is < 2000 characters, it's probably junk, so don't add
		if len(fullarticle) < 2000: return

		data['id'] = journal['id']
		data['golden'] = 0
		data['content'] = re.sub(p, sub, clean)
		print data
		print '\n\n\n'

		writingLock.acquire()
		json.dump(data, outfile)
		outfile.write('\n')
		writingLock.release()

		return 1

	except:
		return


# setup threadpool
pool = ThreadPool(4)

results = pool.map(pull_journal, journals_to_scrape)

pool.close()
pool.join()
	
# output results
print len(results)

outfile.close()
journalfile.close()

