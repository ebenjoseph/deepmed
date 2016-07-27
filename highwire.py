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
TITLE_BODY_PARSABLE = {'abstract', 'intro'}

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


def parse_keywords(root):
	keywords = root.find_all(attrs={'class': re.compile(KEYWORD_ITEM_CLASS)})
	keywords_flattened = []
	for k in keywords:
		keywords_flattened += k.a.contents[0].split(',')	
	
	#TODO: Replace with file output
	for k in keywords_flattened:
		print str(k)	
		
	return

# Custom parsing subroutine for sections that have just title and body, supporting subsections
# that have their own subtitles.  This should work for most abstract / intro / discussion sections.	
def parse_title_body(root):
	subsections = root.find_all(attrs={'class': re.compile('^%s' % SUBSECTION_CLASS)})
	title = title = root.h2.contents[0]
	body = ''
	print 'TITLE: '+title
	
	if len(subsections) > 0:
		for s in subsections:
			subtitle = title+KEY_DELIMITER+s.strong.contents[0]
			#TODO: replace s.strong with something that supports h3 to get Materials
			b = s.p.contents[1]
			print 'SUBTITLE: '+subtitle
			print 'BODY: '+b
			#TODO: Add code here that exports each subtitle / body
	else:
		content = root.find_all(attrs={'id': re.compile('^p-')})
		for c in content:
			print c['id']
			for d in c.contents:
				if isinstance(d, basestring):
					body += d
					body += ' '
		print 'BODY: '+body
		#TODO: Add code here that exports the combined body with the title
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
			if section_type in TITLE_BODY_PARSABLE:
				try:
					parse_title_body(s)
				except:
					print 'ERROR parsing %s' % section_type
			elif section_type == KEYWORD_CLASS:
				try:
					parse_keywords(s)
				except:
					print 'ERROR parsing %s' % section_type			
			else:
				#TODO: implement other custom parsers
					
			
		
	except:
		print 'Error loading article'
	return

pull_article('http://circ.ahajournals.org/content/134/4/270.long')