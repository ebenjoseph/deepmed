#Requires installing selenium (sudo pip install selenium)
#Requires installing PhantomJS (brew install phantomjs)
#Requires a review directory (review/)
import logging
import sys
from bs4 import BeautifulSoup
from selenium import webdriver
from time import sleep
import time
import json
import os
import requests
from multiprocessing.dummy import Pool as ThreadPool # for multithreading

#import re
#import csv
#import re
#import xml.etree.ElementTree

#SET UP LOGGING
#Config the level of information (DEBUG, INFO, WARNING, ERROR, CRITICAL), output location, and formatting of the log
#Create a second handler, change formatting, and appends it to the root to stream log to console
#set logging level from command line. python.py -log=INFO
root = logging.getLogger()
logging.basicConfig(level=logging.INFO, filename='pubmed_harvest_v3.log', format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
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
		web_page = requests.get(root_link)
	except:
		logging.info('Website request failed.')
		logging.debug('Requested link: %s', root_link)
		return -1
	return BeautifulSoup(web_page.content, "lxml")

#Let's go!
logging.info('Program initiated')
logging.debug('Debugging logging active')
#INPUT
#Search Terms for PubMed
search_terms = [
'heart disease'
#'lung cancer'
]

filepath = time.strftime("%Y%m%d-%H%M%S") + "_data.jsonl"
f = open(filepath,'w')

#proxy for Selenium/PhantomJS for access to server
service_args = [
'--proxy=10.254.18.174:3128',
'--proxy-auth=deepmed:deepmed',
'--proxy-type=http'
]

def getlink(reportLink):
	data = {}
	start_time = time.time()

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

	#NEW -- Load the PubMed page (reportPage) using BeautifulSoup4
	soup = getsoup(reportPage)
	logging.info('Report page loaded')
	
	#NEW -- Grab FullTextLink with BS4
	fullTextLink = soup.find('div', class_="icons portlet")
	fullTextLink = fullTextLink.find('a', href=True)['href']
	logging.info('Link to full text article: %s', fullTextLink)

	#write everything we found to the JSON file
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
	data['title'] = title
	data['authors'] = authors
	data['journal_name'] = journalName
	data['journal_code'] = journalNameShort
	data['citation'] = citation
	data['pubmed_page'] = reportPage
	data['fulltext_page'] = fullTextLink
	#data['followed_fulltextlink'] = followed_fulltextlink
	#data['error_nofulltext'] = noFullText
	#data['fulltext'] = fullText
	#data['error_pagesource'] = error_pagesource

	## CHANGE THIS TO CSV OUTPUT ##
	json.dump(data, f, indent=2) # use previously opened file (need it opened before implementing threads)

#set vars that may not get defined
followed_fulltextlink = ''
error_pagesource = ''
counter_item = 1000
#Start the loop
for term in search_terms:

	#Start PhantomJS browser
	logging.info('Starting PhantomJS...')
	layer1 = webdriver.PhantomJS(service_args=service_args) #for use with proxy
	#layer1 = webdriver.PhantomJS() # no proxy
	layer1.set_window_size(1024, 768)
	logging.info('PhantomJS ready')

	logging.info('Searching for: "%s"', term)
	link = 'http://www.ncbi.nlm.nih.gov/pubmed/?term="' + term + '"%5BAll+Fields%5D+AND+"loattrfull+text"%5Bsb%5D'
	#link = 'http://www.ncbi.nlm.nih.gov/pubmed/?term="' + term #testing link to search for simple terms
	layer1.get(link)
	logging.info('Search results loaded')

	pagination = True
	while (pagination == True):

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
#closer out the browser
layer1.close()

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