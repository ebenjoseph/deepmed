import requests
from bs4 import BeautifulSoup
import re
import logging
from datetime import datetime
import csv
import json
import xml.etree.ElementTree
from multiprocessing.dummy import Pool as ThreadPool
import threading
import collections


CONTENT_CLASS = 'article fulltext-view '
SECTION_PREFIX = 'section '
SUBSECTION_CLASS = 'subsection'
KEYWORD_CLASS = 'kwd-group'
KEYWORD_ITEM_CLASS = 'kwd'
KEY_DELIMITER = ': '

def getsoup(root_link):
	try:
		session = requests.Session()
		session.headers = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/600.8.9 (KHTML, like Gecko) Version/8.0.8 Safari/600.8.9'
		#run locally on the arduino, use this:################################################
		#web_page = session.get(root_link)
		#with deepmed proxy for aws, use these:###############################################
		proxies = {
		    "http": "http://myth31.stanford.edu:12345",
		}
		web_page = session.get(root_link, proxies=proxies)
	except:
		logging.info('Error requesting page...')
		return -1
	#return BeautifulSoup(web_page.content, "html.parser") #python's parser
	return BeautifulSoup(web_page.content, "lxml") #lxml (faster)


# Custom parsing subroutine for abstract (copy full text to output)
def parse_abstract(root):
	subsections = root.find_all(attrs={'class': re.compile('^%s' % SUBSECTION_CLASS)})
	for s in subsections:
		subtitle = root['class'][1]+KEY_DELIMITER+s.strong.contents[0]
		body = s.p.contents[1]
		
		#TODO: Replace with file output
		print 'SUBTITLE: '+subtitle
		print 'BODY: '+body
		
	return

# Custom parsing subroutine for keywords
def parse_keywords(root):
	keywords = root.find_all(attrs={'class': re.compile(KEYWORD_ITEM_CLASS)})
	keywords_flattened = []
	for k in keywords:
		keywords_flattened += k.a.contents[0].split(',')	
	
	#TODO: Replace with file output
	for k in keywords_flattened:
		print str(k)	
		
	return

# Custom parsing subroutine for intro (copy full text to output)	
def parse_intro(root):
	print 'PARSE INTRO NOT IMPLEMENTED YET!'
	return
	
# Custom parsin subroutine for materials (copy full text to output, flatten any sub-headers using ': ' as delimiter)	
def parse_materials(root):
	print 'PARSE MATERIALS NOT IMPLEMENTED YET!'
	return

def parse_results(root):
	print 'PARSE RESULTS NOT IMPLEMENTED YET!'
	return

def parse_discussion(root):
	print 'PARSE DISCUSSION NOT IMPLEMENTED YET!'
	return
	
def parse_acknowledgements(root):
	print 'PARSE ACKNOWLEDGEMENTS NOT IMPLEMENTED YET!'
	return
	
def parse_funding(root):
	print 'PARSE FUNDING NOT IMPLEMENTED YET!'
	return

def parse_disclosures(root):
	print 'PARSE DISCLOSURES NOT IMPLEMENTED YET!'
	return
	
def parse_references(root):
	print 'PARSE REFERENCES NOT IMPLEMENTED YET!'
	return			
	
def pull_article(root_link):
	try:
		soup = getsoup(root_link)
		
		# Find full article text
		article = soup.find_all('div',class_=CONTENT_CLASS)[0]
		
		
		# Find Keywords
		kwd = article.find_all(attrs={'class': re.compile(KEYWORD_CLASS)})
		if len(kwd) > 0:
			try:
				parse_keywords(kwd[0])
			except:
				print 'ERROR parsing keywords'	
		
		# Find section headers (children of full article div)	
		for s in article.find_all(attrs={'class': re.compile('^%s' % SECTION_PREFIX)}):
			section_type = s['class'][1]	
			if section_type == 'abstract':
				try:
					parse_abstract(s)
				except:
					print 'ERROR parsing abstract'	
			else:
				#TODO: implement other custom parsers
					
			
		
	except:
		print 'Error loading article'
	return

pull_article('http://circ.ahajournals.org/content/134/4/270.long')