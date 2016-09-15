#Searches pubmed for the title of a study, checks that there is only 1 result, then confirms that the year matches.
#If there is a positive match, the script collects the PubMedID, metadata, and full text links
#It also tracks which Titles/UniqueIDs have already been added to the output file and skips them
import logging
import sys
from bs4 import BeautifulSoup
from selenium import webdriver
from time import sleep
import time
import json
import os
import requests
import csv
from multiprocessing.dummy import Pool as ThreadPool # for multithreading
import collections
from random import choice
import re
from datetime import datetime
import threading

user_agents = [
'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/600.8.9 (KHTML, like Gecko) Version/8.0.8 Safari/600.8.9',
'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36',
'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1',
'Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11',
'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6',
'Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6',
'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/19.77.34.5 Safari/537.1',
'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5',
'Mozilla/5.0 (Windows NT 6.0) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.36 Safari/536.5',
'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3',
'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3',
'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3',
'Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3',
'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3',
'Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3',
'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3',
'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3',
'Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3',
'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24',
'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24'
]

def random_user_agent():
    return choice(user_agents)
#import xml.etree.ElementTree

#SET UP LOGGING
#Config the level of information (DEBUG, INFO, WARNING, ERROR, CRITICAL), output location, and formatting of the log
#Create a second handler, change formatting, and appends it to the root to stream log to console
#set logging level from command line. python.py -log=INFO
root = logging.getLogger()
logging.basicConfig(level=logging.INFO, filename='cochrane_pubmed_mapping.log', format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
streamthelog = logging.StreamHandler(sys.stdout)
streamthelog.setLevel(logging.DEBUG)
streamthelog.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p'))
root.addHandler(streamthelog)

#SET UP XPATH FUNCTION FOR MULTIPLE ATTEMPTS
def getxpath(element, searches):
	for xpath in searches:
		try:
			logging.info('Trying: %s', xpath)
			temp = element.find_element_by_xpath(xpath)
			logging.info('Success! XPath found: %s', temp)
			return temp
		except:
			logging.info('Could not find: %s', xpath)
			continue
	return 'Not found'

def getallxpath(element, searches):
	for xpath in searches:
		try:
			logging.debug('Trying: %s', xpath)
			temp = element.find_elements_by_xpath(xpath)
			logging.debug('Success! XPath found: %s', temp)
			return temp
		except:
			logging.debug('Could not find: %s', xpath)
			continue
	return 'Not found'

def getxpathatt(element, attribute, searches):
	for xpath in searches:
		try:
			logging.debug('Trying: %s', xpath)
			temp = element.find_element_by_xpath(xpath).get_attribute(attribute)
			logging.debug('Success! XPath found: %s', temp)
			return temp
		except:
			logging.debug('Could not find: %s', xpath)
			continue
	return 'Not found'

def getallxpathatt(element, attribute, searches):
	for xpath in searches:
		try:
			logging.debug('Trying: %s', xpath)
			temp = element.find_elements_by_xpath(xpath).get_attribute(attribute)
			logging.debug('Success! XPath found: %s', temp)
			return temp
		except:
			logging.debug('Could not find: %s', xpath)
			continue
	return 'Not found'

def getxpathtext(element, searches):
	for xpath in searches:
		try:
			logging.debug('Trying: %s', xpath)
			temp = element.find_element_by_xpath(xpath).text
			logging.debug('Success! XPath found: %s', temp)
			return temp
		except:
			logging.debug('Could not find: %s', xpath)
			continue
	return 'Not found'

def getallxpathtext(element, searches):
	for xpath in searches:
		try:
			logging.debug('Trying: %s', xpath)
			temp = element.find_element_by_xpath(xpath).text
			logging.debug('Success! XPath found: %s', temp)
			return temp
		except:
			logging.debug('Could not find: %s', xpath)
			continue
	return 'Not found'

def hms_string(sec_elapsed):
    h = int(sec_elapsed / (60 * 60))
    m = int((sec_elapsed % (60 * 60)) / 60)
    s = sec_elapsed % 60.
    return "{}:{:>02}:{:>05.2f}".format(h, m, s)

def getsoup(root_link):
	try:
		session = requests.Session()
		session.headers = random_user_agent()
		web_page = session.get(root_link)
		time.sleep(.25)
	except:
		logging.info('Website request failed.')
		logging.debug('Requested link: %s', root_link)
		return -1
	return BeautifulSoup(web_page.content, "lxml")

def getlink(ref):
	data = collections.OrderedDict()
	start_time = time.time()
	try:
		coch_country = ref['CY']
	except:
		coch_country = 'N/A'
	try:
		coch_author = ref['AU']
	except:
		coch_author = 'N/A'
	try:
		coch_title = ref['TI']
	except:
		coch_title = 'N/A'
	try:
		coch_year = ref['YR']
	except:
		coch_year = 'N/A'
	try:
		coch_source = ref['SO']
	except:
		coch_source = 'N/A'
	try:
		coch_volume = ref['VL']
	except:
		coch_volume = 'N/A'
	try:
		coch_pages = ref['PG']
	except:
		coch_pages = 'N/A'
	try:
		coch_publisher = ref['PB']
	except:
		coch_publisher = 'N/A'
	try:
		coch_number = ref['NO']
	except:
		coch_number = 'N/A'
	try:
		coch_id = ref['id']
	except:
		coch_id = 'N/A'

	#CHECK THE COCH_ID TO SEE IF WE HAVE PULLED BEFORE
	journalLock.acquire()
	try:
		journalsRead[coch_id]
		journalLock.release()
		logging.info('Title found in tracker. Skipping...')
		return
	except:
		journalsRead[coch_id] = 1

	logging.info('Title not found in tracker. Adding to tracker...')
	journalfile.write(coch_id)
	journalfile.write('\n')

	journalLock.release()
	'''
	#Grab details of the Journal
	resultNumber = getxpathtext(reportLink,[".//div[contains(@class,'rprtnum')]"])
	resultNumber = resultNumber.replace('.','')
	logging.info('Result number: %s', resultNumber)

	title = getxpathtext(reportLink,[".//div[contains(@class,'rslt')]//p[@class='title']"])
	logging.info('Journal title: %s', title)

	pmid = getxpathtext(reportLink,[".//dl[@class='rprtid']//dd"])
	logging.info('PMID: %s', pmid)

	authors = getxpathtext(reportLink,[".//p[@class='desc']"])
	logging.info('Authors: %s', authors)
	journalName = getxpathatt(reportLink,"title",[".//span[@class='jrnl']"])
	logging.info('Full journal name: %s', journalName)
	journalNameShort = getxpathtext(reportLink,[".//span[@class='jrnl']"])
	logging.info('Short journal name: %s', journalNameShort)
	citation = getxpathtext(reportLink,[".//p[@class='details']"])
	logging.info('Citation: %s', citation)


	reportPage = getxpathatt(reportLink,"href",[".//p[@class='title']/a"])
	logging.info('Loading report page: %s', reportPage)
	'''

	#Load the PubMed page (reportPage) using BeautifulSoup4
	logging.info('Target article: %s', coch_title)
	logging.info('Loading page with BS4...')
	coch_title = coch_title.replace(" ","%20")
	reportLink = 'http://www.ncbi.nlm.nih.gov/pubmed/?term="' + coch_title + '"'
	soup = getsoup(reportLink)
	logging.info('Page loaded')

	#Check for only 1 result
	#if 1 result, then collect metadata (match = 1)
	#if multiple results or no results, then skip metadat (match = 0)
	match = 0
	try:
		resultcount = soup.find('div',class_='content').find('h3').get_text().replace("\n","")
		if resultcount[:4] == 'See ':
			logging.info('Number of results: %s', resultcount)
			resultcount = '1'
			match = 1
		elif resultcount[:6] == 'Items:':
			logging.info('Multiple results returned')
			resultcount = 'MultipleResults'
			match = 0
		elif resultcount == 'Author information':
			logging.info('Number of results: %s', resultcount)
			resultcount = '1'
			match = 0
		else:
			logging.info('first No results returned')
			resultcount = 'NoResults'
			match = 0
	except:
		try:
			resultcount = soup.find('li',class_='info icon').find('span',class_='icon').get_text().replace("\n","")
			if resultcount == 'No items found.':
				logging.info('second No results returned')
				resultcount = 'NoResults'
				match = 0
			else:
				logging.info('Quoted phrase not found, but matched')
				resultcount = '1'
				match = 1
		except:
			logging.info('third No results returned')
			resultcount = 'NoResults'	
			match = 0

	if match == 1:
		#Grab meta data
		try:
			pmid = soup.find('a',ref='aid_type=pmid').get_text()
			logging.info('PMID: %s', pmid)
		except:
			pmid = 'Not found'
			logging.info('Could not find PMID.')

		try:
			title = soup.find('div',class_='rprt_all').find('h1').get_text()
			logging.info('Journal title: %s', title)
		except:
			title = 'Not found'
			logging.info('Could not find Journal title.')

		try:
			journalName = soup.find('div',class_="cit").find('a')['title']
			logging.info('Full journal name: %s', journalName)
		except:
			journalName = 'Not found'
			logging.info('Could not find Full journal name.')

		try:
			journalNameShort = soup.find('div',class_="cit").find('a').get_text()
			logging.info('Short journal name: %s', journalNameShort)
		except:
			journalNameShort = 'Not found'
			logging.info('Could not find Short journal name.')

		try:
			citation = soup.find('div',class_="cit").get_text()
			logging.info('Citation: %s', citation)
		except:
			citation = 'Not found'
			logging.info('Could not find citation.')

		#Grab FullTextLink
		try:
			fullTextLink = soup.find('div', class_="linkoutlist")
			fullTextLink = fullTextLink.find('h4', text=re.compile('Full Text Sources')).next_sibling
			full_links = fullTextLink.findAll('a')
			fullTextLinks = []
			for each in full_links:
				temp = [each.get_text(),each['href']]
				fullTextLinks.append(temp)
			logging.info('Collected full text links.')
		except:
			fullTextLinks = 'Not found'

		##Grab publication types
		try:
			ptype = soup.find('h4', text='Publication Types').next_sibling
			ptype = ptype.findAll('li')
			pubtypes = []
			temp = -1
			for num in ptype:
				temp += 1
				pubtypes.append(ptype[temp].get_text())
		except:
			pubtypes = 'Not found'

		logging.info('Pubtypes: %s', pubtypes)

		try:
			pubdate = citation[len(journalNameShort)+1:]
			try:
				temp = pubdate.find(";")
			except:
				temp = pubdate.find(".")
			pubdate = pubdate[:temp]

			try:
				pubdate = datetime.strptime(pubdate,'%Y %b %d')
			except:
				pubdate = datetime.strptime(pubdate,'%Y %b')
		except:
			pubdate = 'Not found'

		logging.info('Publication date: %s', pubdate)

		##Grab MeSH Terms
		try:
			mterms = soup.find('h4', text='MeSH Terms').next_sibling
			mterms = mterms.findAll('li')
			meshterms = []
			temp = -1
			for num in mterms:
				temp += 1
				meshterms.append(mterms[temp].get_text().encode("utf-8"))
		except:
			meshterms = 'Not found'

		logging.info('MeSH Terms: %s', meshterms)

		##Grab substances
		try:
			subs = soup.find('h4', text='Substances').next_sibling
			subs = subs.findAll('li')
			substances = []
			temp = -1
			for num in subs:
				temp += 1
				substances.append(subs[temp].get_text().encode("utf-8"))
		except:
			substances = 'Not found'

		logging.info('Substances: %s', substances)

		##Grab Grant Support
		try:
			gsup = soup.find('h4', text='Grant Support').next_sibling
			gsup = gsup.findAll('li')
			grantsupport = []
			temp = -1
			for num in gsup:
				temp += 1
				grantsupport.append(gsup[temp].get_text().encode("utf-8"))
		except:
			grantsupport = 'Not found'

		logging.info('Grants: %s', grantsupport)
		
		##Grab authors and affiliations
		try:
			try:
				aff = soup.find('div', class_="afflist")
				aff = aff.findAll('li')
				affiliations = []
				temp = -1
				for num in aff:
					temp += 1
					affiliations.append(aff[temp].get_text()[1:])
			except:
				affiliations = 'Not found'
			##Get authors and match with affiliation
			auth = soup.find('div', class_="auths")
			auth = auth.findAll('a', href=True)
			authorsaff = []
			temp = -1
			for num in auth:
				temp += 1
				try:
					#check for multiple numbers and merge them if they exist
					idx = []
					if "," in auth[temp].next_sibling.get_text():
						idx.append(auth[temp].next_sibling.get_text()[:-1])
						if "," in auth[temp].next_sibling.next_sibling.get_text():
							idx.append(auth[temp].next_sibling.next_sibling.get_text()[:-1])
							if "," in auth[temp].next_sibling.next_sibling.next_sibling.get_text():
								idx.append(auth[temp].next_sibling.next_sibling.next_sibling.get_text()[:-1])
								if "," in auth[temp].next_sibling.next_sibling.next_sibling.next_sibling.get_text():
									idx.append(auth[temp].next_sibling.next_sibling.next_sibling.next_sibling.get_text()[:-1])
									if "," in auth[temp].next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.get_text():
										idx.append(auth[temp].next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.get_text()[:-1])
									else:
										idx.append(auth[temp].next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.get_text())
								else:
									idx.append(auth[temp].next_sibling.next_sibling.next_sibling.next_sibling.get_text())
							else:
								idx.append(auth[temp].next_sibling.next_sibling.next_sibling.get_text())
						else:
							idx.append(auth[temp].next_sibling.next_sibling.get_text())
					else:
						idx.append(auth[temp].next_sibling.get_text())
					fil = ""
					counter = -1
					for idc in idx:
						counter += 1
						if counter == 0:
							fil = affiliations[int(idc)-1]
						else:
							fil = fil + "; " + affiliations[int(idc)-1]
					authorsaff.append([auth[temp].get_text().encode("utf-8"),fil.encode("utf-8")])
				except:
					authorsaff.append([auth[temp].get_text().encode("utf-8"),'Not found'])
		except:
			authorsaff = 'Not found'
		
		logging.info('Authors and affiliations: %s', authorsaff)
	else:
		x = 0

	#Check if the year matches
	try:
		if int(pubdate.year) == int(coch_year):
			yearmatch = 'Y'
		else:
			yearmatch = 'N'
	except:
		yearmatch = 'N/A'
	#Check if the author matches
	authormatch = 'N'
	try:
		if authorsaff[0][0].encode("utf-8") in coch_author.encode("utf-8"):
			authormatch = 'Y'
	except:
		authormatch = 'N/A'
	data = {}
	data['results'] = resultcount
	data['yearmatch'] = yearmatch
	data['authormatch'] = authormatch
	#pass through the cochrane data
	data['coch_id'] = coch_id
	data['coch_title'] = coch_title
	data['coch_country'] = coch_country
	data['coch_author'] = coch_author
	data['coch_title'] = coch_title
	data['coch_year'] = coch_year
	data['coch_source'] = coch_source
	data['coch_volume'] = coch_volume
	data['coch_pages'] = coch_pages
	data['coch_publisher'] = coch_publisher
	data['coch_number'] = coch_number
	#write everything we found to JSON file
	if match == 1:
		data['pmid'] = pmid
		data['title'] = title.encode("utf-8")
		data['authors'] = authorsaff
		data['affiliations'] = affiliations
		data['journal_name'] = journalName.encode("utf-8")
		data['journal_code'] = journalNameShort.encode("utf-8")
		data['pubtypes'] = pubtypes
		data['meshterms'] = meshterms
		data['citation'] = citation.encode("utf-8")
		data['pubdate'] = str(pubdate)
		data['pubmed_page'] = reportLink
		data['fulltext_page'] = fullTextLinks
	writingLock.acquire()
	json.dump(data, outfile) # use previously opened file (need it opened before implementing threads)
	outfile.write('\n')
	writingLock.release()

# Let's go!
logging.info('Program initiated')
logging.debug('Debugging logging active')

# define new tracker
articletracker = 'cochrane_pubmed_mapping_tracker'

# read in previously read journal links
journalsRead = {}
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

# open or create output file
outfile = open('cochrane_pubmed_mapping.jsonl', 'a')


refs_to_pull = []
# read in JSON
with open('cochrane_refs.jsonl') as data_file:
	for line in data_file:
		inputdata = json.loads(line)
		refs_to_pull.append(inputdata)

# setup threadpool
pool = ThreadPool(4)
results = pool.map(getlink, refs_to_pull)
pool.close()
pool.join()
# output results
logging.info(len(results))