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
import traceback


CONTENT_CLASS = 'article fulltext-view '
REFERENCE_CLASS = 'ref-list'
SECTION_PREFIX = 'section '
SUBSECTION_CLASS = 'subsection'
KEYWORD_CLASS = 'kwd-group'
KEYWORD_ITEM_CLASS = 'kwd'
KEY_DELIMITER = ': '
TITLE_BODY_PARSABLE = {'abstract', 'intro', 'materials', 'results', 'discussion', 'acknowledgments', 'sources_of_funding', 'disclosures'}

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
	keywords_flattened = ''
	title = 'Key words'
	
	for k in keywords:
		keywords_flattened += k.a.contents[0]
		keywords_flattened += ', '
	
	if len(keywords) > 0:
		output = collections.OrderedDict()
		output[title] = keywords_flattened
		return output
		
	return None

def parse_references(root):
	title = root.find(['strong','h2','h3','h4']).contents[0]
	ref_list = root.find(['ol'])
	refs = ref_list.find_all('li')
	output = collections.OrderedDict()
	output_list = []
	print 'PARSING.... %s' % title
	
	for r in refs:
		print r
		output_list.append(r.get_text())
	
	if len(output_list) > 0:
		output[title] = output_list
		return output
				
	return None

# Custom parsing subroutine for sections that have just title and body, supporting subsections
# that have their own subtitles.  This should work for most abstract / intro / discussion sections.	
def parse_title_body(root):
	subsections = root.find_all(attrs={'class': re.compile('^%s' % SUBSECTION_CLASS)})
	title = root.find(['strong','h2','h3','h4']).contents[0]
	output = collections.OrderedDict()
	print 'PARSING.... %s' % title
	
	if len(subsections) > 0:
		# Case: There is at least 1 subsection in this section of the article	
		for s in subsections:			
			subtitle = s.find(['strong','h2','h3','h4']).contents[0]
			subsubsections = s.find_all(attrs={'class': re.compile('^%s' % SUBSECTION_CLASS)})
			
			if len(subsections) > 0:
				for ss in subsubsections:
					subsubtitle = ss.find(['strong','h2','h3','h4']).contents[0]
					body = ss.p.contents[1]
					if body != None:
						key = title
						if subtitle != None:
							key += KEY_DELIMITER
							key += subtitle
						if subsubtitle != None:
							key += KEY_DELIMITER
							key += subsubtitle	
						output[key] = body
			if s.p.contents != None and len(s.p.contents) > 1:	
				body = s.p.contents[1]
			if body != None:
				if subtitle != None:
					key = title+KEY_DELIMITER+subtitle
					output[key] = body
			
	else:
		body = ''
		content = root.find_all(attrs={'id': re.compile('^p-')})
		for c in content:
			#print c['id']
			for d in c.contents:
				if isinstance(d, basestring):
					body += d
					body += ' '
		
		# Case when there are no subsections: output body as key to title
		output[title] = body
				
	return output
		
	
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
					#parse_title_body(s)
					print 'Parsed section: %s' % section_type
				except Exception as e:
					print 'ERROR parsing %s' % section_type
					print e.__doc__
					tb = traceback.format_exc()
					print tb
					
			elif section_type == KEYWORD_CLASS:
				try:
					parse_keywords(s)
					print 'Parsed section: %s' % section_type
				except Exception as e:
					print 'ERROR parsing %s' % section_type
					print e.__doc__
					tb = traceback.format_exc()
					print tb
			
			elif section_type == REFERENCE_CLASS:
				try:
					parse_references(s)
					print 'Parsed section: %s' % section_type
				except Exception as e:
					print 'ERROR parsing %s' % section_type
					print e.__doc__
					tb = traceback.format_exc()
					print tb		
					
			else:
				print 'UNSUPPORTED SECTION: %s' % section_type
				#TODO: implement other custom parsers
	except:
		print 'Error loading article'
	return

pull_article('http://circ.ahajournals.org/content/134/4/270.long')