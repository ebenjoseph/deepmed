#Requires installing selenium (sudo pip install selenium)
#Requires installing PhantomJS (brew install phantomjs)
#Requires a review directory (review/) if using the "follow fulltext links"
import logging
import sys
from bs4 import BeautifulSoup
from selenium import webdriver
from time import sleep
import time
#import json
import os
import requests
import csv

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

#Let's go!
logging.info('Program initiated')
logging.debug('Debugging logging active')
#INPUT
#Search Terms for PubMed
search_terms = [
'heart disease'
#'lung cancer'
#'cancer hypothesis', #60 results for pagination tests
#'stress inducated taxation', #0 results for tests
]

#proxy for Selenium/PhantomJS for access to server
service_args = [
'--proxy=10.254.18.174:3128',
'--proxy-auth=deepmed:deepmed',
'--proxy-type=http'
]

#set vars that may not get defined
followed_fulltextlink = ''
error_pagesource = ''
counter_item = 1000

#Start PhantomJS browser
logging.info('Starting PhantomJS...')
layer1 = webdriver.PhantomJS(service_args=service_args) #for use with proxy
#layer1 = webdriver.PhantomJS() # no proxy
layer1.set_window_size(1024, 768)
logging.info('PhantomJS ready')

#Start the loop
for term in search_terms:
	#set the output for this search term
	filepath = time.strftime("%Y%m%d-%H%M%S") + "_" + term + "_data.csv"
	f = open(filepath,'w')
	f.close()

	logging.info('Searching for: "%s"', term)
	link = 'http://www.ncbi.nlm.nih.gov/pubmed/?term="' + term + '"%5BAll+Fields%5D+AND+"loattrfull+text"%5Bsb%5D'
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

		#loop through each search result
		for reportLink in searchResults:
			data = {}
			start_time = time.time()
			counter_item += 1
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

			#OLD -- Load PubMed Page in Selenium/PhantomJS
			#layer2 = webdriver.PhantomJS(service_args=service_args) #for use with proxy
			#layer2 = webdriver.PhantomJS() #no proxy
			#layer2.set_window_size(1024, 768)
			#layer2.get(reportPage)
			logging.info('Report page loaded')
			
			#OLD -- Grab FullTextLink with Sel/Phan
			#fullTextLink = getxpathatt(layer2,"href",["//div[@class='icons portlet']//a"])
			#NEW -- Grab FullTextLink with BS4
			try:
				fullTextLink = soup.find('div', class_="icons portlet")
				fullTextLink = fullTextLink.find('a', href=True)['href']
			except:
				fullTextLink = 'Not found'
				continue
			logging.info('Link to full text article: %s', fullTextLink)

			'''
			### Follow the full text link and check for full text
			if (fullTextLink == 'Not found'):
				logging.info('No full text links found on report page.')
			else:
				logging.info('Loading full text article link: %s', fullTextLink)
				layer3 = webdriver.PhantomJS(service_args=service_args) # for use with proxy
				#layer3 = webdriver.PhantomJS() # no proxy
				layer3.set_window_size(1024, 768)
				layer3.get(fullTextLink)
				logging.info('Full text page loaded')

				#check to see if there are deeper links required and navigate to them
				logging.info('Checking for deeper links to full text...')
				xpath_deeper = [
				'//a[@title="Link to article fulltext"]',
				'//a[text()="Full Text"]',
				'//a[@class="viewFullTextLink"]',
				'//div[@class="tabs print-hide"]//a[text()="Fulltext"]',
				'//a[@onmouseover="window.status=\'LWWOnline\';return true"]',
				'//a[@onmouseover="window.status=\'Ovid\';return true"]'
				#//a[text()="Fulltext"]'
				]
				
				deeperlink1 = getxpath(layer3,xpath_deeper)
				if not (deeperlink1 == 'Not found'):
					#deeper link found, follow it
					logging.info('Deeper link found')
					logging.info('Clicking deeper link: %s', deeperlink1)
					deeperlink1.click()
					logging.info('Deeper link loaded')
					followed_fulltextlink = 'Yes'

				#Do we want to check for a second level of links? Guess is no due to possible loops.
				#For now, we'll leave it as-is and review the first round of output

				#check to see if this is explicitly NOT the full text (requires sign-in, payment, membership, etc.)
				logging.info('Checking if article is available or requires login/payment...')
				xpath_unavailable = [
				"//div[@class='denialInfo']//h2",
				"//div[@id='accessDenied']//h2",
				"//div[contains(@class,'access_no accessIcon')]",
				"//div[@id='ppv']//div[@class='article-info-login']",
				'//a[contains(text(),"to access the full article.")]'
				#search by text: //div[@class='society-member-title']/strong["To access this article"]
				]

				noFullText = getxpathtext(layer3,xpath_unavailable)
				if not (noFullText == 'Not found'):
					logging.info('Full text not available: paid/requires login')
				else:
					logging.info('Full text probably available. Searching for full text...')

					xpath_fulltext = [
					'//div[@itemprop="articleBody"',
					'//div[contains(@class,"article fulltext-view")]',
					'//div[@id="main"]/div[@id="content"]//div[@id="articleHTML"]',
					'//div[@id="productContent"]//div[@id="fulltext"]',
					'//div[@class="art-box art-post"]//div[@class="WordSection1"]',
					'//div[@class="tab-content"]/div[@class="articles"]', #dovepress.com,
					'//div[@id="centerInner" and aria-label="Article"]', #ScienceDirect.com
					'//div[@id="artTabContent"]' #InternationalJournalOfCardiology.com
					#'//div[@id="articleHTML"]',
					#'//div[@id="fulltext"]'
					]
					
					fullText = getxpathtext(layer3,xpath_fulltext)
					if (fullText == 'Not found'):
						logging.info('Full text not found. Bad Xpath, requires login, or does not exist.')
						logging.info('Saving HTML for review...')
						filename_html = 'review/' + time.strftime("%Y%m%d-%H%M%S") + "_PMID" + str(pmid) + '.html'
						logging.info('Opening file to write: %s', filename_html)
						f = open(filename_html,'w')
						error_pagesource = layer3.page_source.encode('utf-8')
						f.write(error_pagesource)
						f.close()
						logging.info('Written and closed: %s', filename_html)
						
						#save screencap with Date, Time and PMID
						logging.info('Taking screenshot for review')
						filename_ss = 'review/' + time.strftime("%Y%m%d-%H%M%S") + "_PMID" + str(pmid) + '.png'
						layer3.save_screenshot(filename_ss)
						
					else:
						logging.info('Full text found')
			'''	

			'''		
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
			'''
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
			data['authors'] = authors.encode("utf-8")
			data['journal_name'] = journalName.encode("utf-8")
			data['journal_code'] = journalNameShort.encode("utf-8")
			data['citation'] = citation.encode("utf-8")
			data['pubmed_page'] = reportPage
			data['fulltext_page'] = fullTextLink
			#data['followed_fulltextlink'] = followed_fulltextlink
			#data['error_nofulltext'] = noFullText
			#data['fulltext'] = fullText
			#data['error_pagesource'] = error_pagesource
			with open (filepath, mode='a') as csvfile:
				wr = csv.DictWriter(csvfile,data.keys(),dialect=csv.excel)
				wr.writerow(data)
			#with open (filepath, mode='a') as outfile: #output to jsonfile in json format
			#	json.dump(data, outfile, indent=2) #output to jsonfile in json format
		
		pagebutton = getxpath(layer1, ['//a[contains(@class,"active") and contains(@class,"next")]','//a[text()="Next >"]'])
		if not (pagebutton == 'Not found'):
			pagebutton.click()
		else:
			pagination = False
#closer out the browser
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