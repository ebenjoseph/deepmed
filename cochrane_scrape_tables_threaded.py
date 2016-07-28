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
import collections

journals_to_scrape = []
##												 ##
##   UPDATE JSON OUTPUT FILE WITH EACH LIBRARY   ##
##												 ##
outfile = open('cochrane_table_output.jsonl', 'a')

# read in csv
with open('Cochrane_harvest_charstudies_output.csv', 'rU') as csvfile:
	reader = csv.reader(csvfile, delimiter=',')
	counter = 0
	for row in reader:
		data = collections.OrderedDict()
		if not counter:
			counter += 1
			continue
		#data['run_id'] = row[0]
		data['link'] = row[0]
		journals_to_scrape.append(data)

#counter = 0
#docs = []
##												 		##
##  UPDATE ARTICLE CHECKING FILENAME WITH EACH LIBRARY  ##
##												 		##
articletracker = 'cochrane_table_tracker'

#p = re.compile(ur'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', re.MULTILINE)
#sub = u"\n\n"
journalsRead = {}

# read in previously read journal links
try:
	journalfile = open(articletracker, 'r')
	for line in journalfile:
		journalsRead[line.rstrip()] = 1
	journalfile.close()
except:
	journalfile = open(articletracker, 'w')
	journalfile.close()
journalfile = open(articletracker, 'a')

journalLock = threading.Lock()
writingLock = threading.Lock()

# setup logging
root = logging.getLogger()
logging.basicConfig(filename='cochrane_table_log.log',level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
streamthelog = logging.StreamHandler(sys.stdout)
streamthelog.setLevel(logging.INFO)
streamthelog.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p'))
root.addHandler(streamthelog)

def getsoup(root_link):
	try:
		session = requests.Session()
		session.headers = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/600.8.9 (KHTML, like Gecko) Version/8.0.8 Safari/600.8.9'
		#run locally, use this:################################################
		web_page = session.get(root_link)
		#with deepmed proxy for aws, use these:###############################################
		#proxies = {
		#'http': 'myth16.stanford.edu:12345'
		#}	
		#web_page = session.get(root_link, proxies=proxies)
	except:
		logging.info('Error requesting page...')
		return -1
	sleep(2)
	#return BeautifulSoup(web_page.content, "html.parser") #python's parser
	return BeautifulSoup(web_page.content, "lxml") #lxml (faster)

def pull_journal(journal):
	root_link = journal['link']
	
	if not len(journalsRead) % 10: print len(journalsRead)

	journalLock.acquire()
	try:
		journalsRead[root_link]
		journalLock.release()
		print 'Article found in tracker. Skipping...'
		return
	except:
		journalsRead[root_link] = 1

	logging.info('Article not found in tracker. Adding to tracker...')
	journalfile.write(root_link)
	journalfile.write('\n')

	journalLock.release()
	
	'''
	Sample links
	http://onlinelibrary.wiley.com/doi/10.1002/14651858.CD006478.pub2/full
	root_link = 'http://onlinelibrary.wiley.com/doi/10.1002/14651858.CD006478.pub2/full'
	'''
	try:
		logging.info("Loading article: %s", root_link)
		soup = getsoup(root_link)
		logging.info("Article loaded...")

		#First, grab the list of references (title, citation, and pubmedurl if available)
		logging.info("Finding references...")
		allrefs = soup.findAll('h4',class_='reference__title')
		for refs in allrefs:
			if refs.find(text=re.compile('studies included')):
				included_refs = refs
				break
		logging.info("Found references for included studies")
		bibs = included_refs.next_sibling.findAll('div',class_='bibSection')
		refs_list = []
		for bib in bibs:
			ref_data = collections.OrderedDict()
			#grab bib title
			try:
				title = bib.find('h5',class_='reference__title').get_text()
				temp = title.find(' {')
				if not (temp == -1):
					title = title[:temp]	
			except:
				title = 'Not found'
			#grab bib full citation
			try:
				citation = bib.find('cite').get_text().strip()
			except:
				citation = 'Not found'
			#grab pubmed url
			try:
				pubmedurl = bib.find('a',text='PubMed')['href']
			except:
				pubmedurl = 'Not found'
			ref_data['title'] = title
			ref_data['citation'] = citation
			ref_data['pubmedurl'] = pubmedurl
			refs_list.append(ref_data)
			logging.info("Captured reference data.")
		logging.info("Captured all references of included studies")
		#Next, we grab the table data
		logging.info("Grabbing data from bias tables")
		alltables = soup.find('h3', text=re.compile('Characteristics of included studies')).next_siblings
		tables_list = []
		table_data = collections.OrderedDict()
		table_count = 0
		for table in alltables:
			#grab table name
			title = table.find('h4').get_text()
			#grab table data
			biastable = table.find('b',text='Bias').parent.parent.next_siblings
			for each in biastable:
				try:
					key = each.find('td')
					key = key.get_text()
					try:
						rating = each.find('td').next_sibling
						rating = rating.get_text()
						try:
							rationale = each.find('td').next_sibling.next_sibling
							rationale = rationale.get_text()
						except:
							rationale = ''
					except:
						rating = ''
						rationale = ''
					table_data[key] = [rating,rationale]
				except:
					continue
			citation = refs_list[table_count]['citation']
			pubmedurl = refs_list[table_count]['pubmedurl']
			bibtitle = refs_list[table_count]['title']
			data = [pubmedurl,citation,table_data]
			tables_list.append(data)
			logging.info("Captured table data.")
			table_count += 1
		
		logging.info("Writing to file...")
		writingLock.acquire()
		for each in tables_list:
			data = collections.OrderedDict()
			data['ReviewURL'] = root_link
			data['pubmedurl'] = each[0]
			data['citation'] = each[1]
			data['table'] = each[2]
			json.dump(data, outfile)
			outfile.write('\n')
		writingLock.release()
		logging.info("Article added!")

		return 1

	except:
		logging.info("Error! Could not parse or could not output to JSON")
		logging.info(root_link)
		return

logging.info("Scraper started at " + str(datetime.now()) )
# setup threadpool
pool = ThreadPool(2)

results = pool.map(pull_journal, journals_to_scrape)

pool.close()
pool.join()
	
# output results
print len(results)

logging.info("Run finished. Processed %s reviews.", len(results))
outfile.close()
journalfile.close()

