#Requires installing selenium (sudo pip install selenium)
#Requires installing PhantomJS (brew install phantomjs)
#Requires a review directory (review/) if using the "follow fulltext links"
import logging
import sys
from bs4 import BeautifulSoup
from selenium import webdriver
from time import sleep
import time
from datetime import datetime
#import json
import os
import requests
import csv
from multiprocessing.dummy import Pool as ThreadPool # for multithreading
import collections

#import re
#import xml.etree.ElementTree

#SET UP LOGGING
#Config the level of information (DEBUG, INFO, WARNING, ERROR, CRITICAL), output location, and formatting of the log
#Create a second handler, change formatting, and appends it to the root to stream log to console
#set logging level from command line. python.py -log=INFO
root = logging.getLogger()
logging.basicConfig(level=logging.INFO, filename='pubmed_harvest_library.log', format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
streamthelog = logging.StreamHandler(sys.stdout)
streamthelog.setLevel(logging.DEBUG)
streamthelog.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p'))
root.addHandler(streamthelog)

#SET UP XPATH FUNCTION FOR MULTIPLE ATTEMPTS
def getxpath(element, searches):
	for xpath in searches:
		try:
			logging.debug('Trying: %s', xpath)
			temp = element.find_element_by_xpath(xpath)
			logging.debug('Success! XPath found: %s', temp)
			return temp
		except:
			logging.debug('Could not find: %s', xpath)
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
		web_page = requests.get(root_link)
	except:
		logging.info('Website request failed.')
		logging.debug('Requested link: %s', root_link)
		return -1
	return BeautifulSoup(web_page.content, "lxml")

def getlink(reportLink):
	#loop through each search result
	#data = {}
	data = collections.OrderedDict()
	start_time = time.time()
	#counter_item += 1
	#Grab details of the Journal
	resultNumber = getxpathtext(reportLink,[".//div[contains(@class,'rprtnum')]"])
	resultNumber = resultNumber.replace('.','')
	logging.info('Result number: %s', resultNumber)
	
	title = getxpathtext(reportLink,[".//div[contains(@class,'rslt')]//p[@class='title']"])
	logging.info('Journal title: %s', title)
	
	pmid = getxpathtext(reportLink,[".//dl[@class='rprtid']//dd"])
	logging.info('PMID: %s', pmid)

	#authors = getxpathtext(reportLink,[".//p[@class='desc']"])
	#logging.info('Authors: %s', authors)
	#authors = authors.replace('.','')
	#authors = authors.split(",")

	journalName = getxpathatt(reportLink,"title",[".//span[@class='jrnl']"])
	logging.info('Full journal name: %s', journalName)

	journalNameShort = getxpathtext(reportLink,[".//span[@class='jrnl']"])
	logging.info('Short journal name: %s', journalNameShort)

	citation = getxpathtext(reportLink,[".//p[@class='details']"])
	logging.info('Citation: %s', citation)

	try:
		pubdate = citation[len(journalNameShort)+2:]
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

	reportPage = getxpathatt(reportLink,"href",[".//p[@class='title']/a"])
	logging.info('Loading report page: %s', reportPage)

	#Load the PubMed page (reportPage) using BeautifulSoup4
	soup = getsoup(reportPage)
	logging.info('Report page loaded')
		

	#Grab FullTextLink
	try:
		fullTextLink = soup.find('div', class_="linkoutlist")
		fullTextLink = fullTextLink.find('a', href=True, text=libraryxpath)['href']
	except:
		fullTextLink = 'Not found'

	logging.info('Link to full text article: %s', fullTextLink)

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
	
	#PROPER LEVEL
	logging.info('Authors and affiliations: %s', authorsaff)

	#write everything we found to the CSV file
	end_time = time.time()
	elapsed = hms_string(end_time - start_time)
	data['run_id'] = counter_item
	data['time_start'] = start_time
	data['time_end'] = end_time
	data['time_elapsed'] = elapsed
	data['search_term'] = term
	data['search_results'] = numResults
	data['result_page'] = currentPage
	data['total_pages'] = pageCount
	data['result_number'] = resultNumber
	data['pmid'] = pmid
	data['title'] = title.encode("utf-8")
	data['authors'] = authorsaff
	data['affiliations'] = affiliations
	data['journal_name'] = journalName.encode("utf-8")
	data['journal_code'] = journalNameShort.encode("utf-8")
	data['pubtypes'] = pubtypes
	data['meshterms'] = meshterms
	data['citation'] = citation.encode("utf-8")
	data['pubdate'] = pubdate
	data['pubmed_page'] = reportPage
	data['fulltext_page'] = fullTextLink
	#data['followed_fulltextlink'] = followed_fulltextlink
	#data['error_nofulltext'] = noFullText
	#data['fulltext'] = fullText
	#data['error_pagesource'] = error_pagesource
	with open (filepath, mode='a') as csvfile:
		wr = csv.DictWriter(csvfile,data.keys(),dialect=csv.excel)
		wr.writerow(data)
		
#Let's go!
logging.info('Program initiated')
logging.debug('Debugging logging active')
#INPUT
#Search Terms for PubMed
libraries = [
#'loprovOvid', #COMPLETE!
'loprovWiley',
#'loprovES',
#'loprovHighWire',
#'loprovSpringer',
#'loprovNPG'
]

libraryxpaths = [
#'Ovid Technologies, Inc.', #COMPLETE!
'Wiley',
#'Elsevier Science',
#'HighWire',
#'Springer',
#'Nature Publishing Group'
]

#Libraries
#PMC
# library = "loprovPMC"
# libraryxpath = "PubMed Central"

#Ovid
# "loprovOvid"
# libraryxpath = "Ovid Technologies, Inc."

#Wiley
# "loprovWiley"
# libraryxpath = "Wiley"

#Elsevier
# "loprovES"
# libraryxpath = "Elsevier Science"

#Highwire
# "loprovHighWire"
# libraryxpath = "HighWire"

#Springer
# "loprovSpringer"
# libraryxpath = "Springer"

#Nature
# "loprovNPG"
# libraryxpath = "Nature Publishing Group"

search_terms = [
'Antibiotic',
'Cardiac screening',
'Cervical cancer',
'chronic kidney disease',
'colorectal cancer',
'copd',
'high value care',
'depression',
'diabetes',
'end of life care',
'pulmonary embolism',
'generic medications',
'gerd',
'hematuria',
'inpatient glycemic control',
'insomnia',
'nephrolithiasis',
'obstructive sleep apnea',
'pressure ulcers',
'cancer',
'pelvic examination',
'prostate cancer',
'stable ischemic heart disease',
'urinary incontinence',
'venous thrombembolism' #add more diseases?
]

#proxy for Selenium/PhantomJS for access to server
'''
service_args = [
'--proxy=10.254.18.174:3128',
'--proxy-auth=deepmed:deepmed',
'--proxy-type=http'
]
'''

#set vars that may not get defined
followed_fulltextlink = ''
error_pagesource = ''
counter_item = 1000

#Start PhantomJS browser
logging.info('Starting PhantomJS...')
#layer1 = webdriver.PhantomJS(service_args=service_args) #for use with proxy
layer1 = webdriver.PhantomJS() # no proxy
layer1.set_window_size(1024, 768)
logging.info('PhantomJS ready')
librarypos = 0;

#Start the loop
for library in libraries:
	logging.info('Begin "%s" library pull', library)
	#set the output for this library
	filepath = time.strftime("%Y%m%d-%H%M%S") + "_" + library + "_data.csv"
	f = open(filepath,'w')
	f.close()

	libraryxpath = libraryxpaths[librarypos]
	librarypos += 1

	for term in search_terms:
		logging.info('Searching "%s" library for "%s"', library, term)
		link = 'http://www.ncbi.nlm.nih.gov/pubmed/?term="' + term + '"[All Fields] AND "' + library + '"[Filter] AND "loattrfull text"[sb] AND "humans"[Filter]'
		#link = 'http://www.ncbi.nlm.nih.gov/pubmed/?term="' + term + '"%5BAll+Fields%5D+AND+"loattrfull+text"%5Bsb%5D+AND+"' + subterm + '"'
		#link = 'http://www.ncbi.nlm.nih.gov/pubmed/?term="' + term + '"%5BAll+Fields%5D+AND+"loattrfull+text"%5Bsb%5D+AND+"' + subterm + '"'
		#link = 'http://www.ncbi.nlm.nih.gov/pubmed/?term="' + term #testing link to search for simple terms
		layer1.get(link)
		logging.info('Search results loaded')

		#start the pagination loop
		pagination = True
		while (pagination == True):

			#check number of results shown per page
			logging.info('Checking the number of results per page...')
			showResults = getxpathtext(layer1,["//a[contains(@data-jigconfig,'#display_settings_menu_ps')]"])
			logging.info('Results per page: %s', showResults)
			if not (showResults == 'Not found'):
				if not (showResults == '200 per page'):
					#click
					logging.info('Changing to 200 results per page...')
					showResultsButton = getxpath(layer1,["//a[contains(@data-jigconfig,'#display_settings_menu_ps')]"])
					showResultsButton.click()
					sleep(1)
					showResultsButton2 = getxpath(layer1,["//input[@id='ps200']"])
					showResultsButton2.click()
					logging.info('Showing 200 results per page')
			else:
				logging.info('Less than 20 results, no pagination required')

			#Get the number of results
			numResults = getxpathatt(layer1,"value",["//input[@id='resultcount']"])
			logging.info('Articles found: %s', numResults)

			#Grab the current page number
			currentPage = getxpathatt(layer1,"value",["//input[@id='pageno']"])
			pageCount = getxpathatt(layer1,"last",["//input[@id='pageno']"])
			logging.info('Current page: %s/%s', currentPage, pageCount)

			#grab all the report links on this search result page
			searchResults = getallxpath(layer1,["//div[@class='rprt']"])

			# setup threadpool
			pool = ThreadPool(4)
			results = pool.map(getlink, searchResults)
			pool.close()
			pool.join()

			pagebutton = getxpath(layer1, ['//a[contains(@class,"active") and contains(@class,"next")]','//a[text()="Next >"]'])
			if not (pagebutton == 'Not found'):
				pagebutton.click()
			else:
				pagination = False

#close out the browser
layer1.close()
logging.info('Program completed successfully')

'''
#Other selenium commands:
#driver.save_screenshot('screen.png') # save a screenshot to disk
#print searchResults[0].get_attribute('innerHTML') #reports out the HTML of something you found
#print searchResults[0].text #prints out the text of the element you found
#print searchResults[0].get_attribute('class') #prints out the value of the attribute Class in the element you found
#http://selenium-python.readthedocs.io/locating-elements.html
#Navigate to next page
#sbtn = driver.find_element_by_class_name('next')
#sbtn.click()

'''
