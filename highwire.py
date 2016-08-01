import requests
import sys
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

# Constants specific to article sections (can be easily changed for non-Highwire articles)
CONTENT_CLASS = 'article fulltext-view '
REFERENCE_CLASS = 'ref-list'
SECTION_PREFIX = 'section'
SUBSECTION_CLASS = 'subsection'
KEYWORD_CLASS = 'kwd-group'
KEYWORD_ITEM_CLASS = 'kwd'
FOOTNOTE_CLASS = 'fn-group'
KEY_DELIMITER = ': '
TITLE_BODY_PARSABLE = {'abstract', 'intro', 'materials', 'results', 'discussion', 'acknowledgments', 'sources_of_funding', 'disclosures'}


# Set up logging
root = logging.getLogger()
logging.basicConfig(filename='scraping_log.log',level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
streamthelog = logging.StreamHandler(sys.stdout)
streamthelog.setLevel(logging.INFO)
streamthelog.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p'))
root.addHandler(streamthelog)


# Method for getting an instance of the BeautifulSoup HTML scraping library
def getsoup(root_link):
	try:
		session = requests.Session()
		session.headers = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/600.8.9 (KHTML, like Gecko) Version/8.0.8 Safari/600.8.9'
		#run locally on the arduino, use this:################################################
		#web_page = session.get(root_link)
		#with deepmed proxy for aws, use these:###############################################
		proxies = {
		    "http": "http://myth32.stanford.edu:12345",
		}
		web_page = session.get(root_link, proxies=proxies)
	except:
		logging.info('Error requesting page...')
		return -1
	#return BeautifulSoup(web_page.content, "html.parser") #python's parser
	return BeautifulSoup(web_page.content, "lxml") #lxml (faster)

# Custom parsing subroutine for the list of keywords in the article.  Outputs a dictionary with 'key words' as key and a flattened, comma separated string of all keywords as value.
def parse_keywords(root):
	keywords = root.find_all(attrs={'class': re.compile(KEYWORD_ITEM_CLASS)})
	keywords_flattened = ''
	title = 'Key words'
	logging.info('PARSING.... %s' % title)
	
	for k in keywords:
		keywords_flattened += k.a.contents[0]
		keywords_flattened += ', '
	
	if len(keywords) > 0:
		output = collections.OrderedDict()
		output[title] = keywords_flattened
		return output
		
	return None

# Custom parsing subroutine for the list of references for the article.  Outputs a dictionary keyed by 'References' and with a single array with all references as value
def parse_references(root):
	title = root.find(['strong','h2','h3','h4']).contents[0]
	ref_list = root.find(['ol'])
	refs = ref_list.find_all('li', recursive=False)
	output = collections.OrderedDict()
	output_list = []
	logging.info('PARSING.... %s' % title)
	
	for r in refs:
		output_list.append(r.get_text())
	
	if len(output_list) > 0:
		output[title] = output_list
		return output
				
	return None

# Custom parsing subroutine for the list of footnotes for the article.  Outputs a dictionary keyed by 'Footnotes' and with a single array with all footnotes as value
#UPDATE: Parser creates a string of Footnotes and outputs as string.
def parse_footnotes(root):
	title = root.find(['strong','h2','h3','h4']).contents[0]
	fn_list = root.find(['ul'])
	footnotes = fn_list.find_all('li', recursive=False)
	output = collections.OrderedDict()
	output_list = ''
	logging.info('PARSING.... %s' % title)
	
	for f in footnotes:
		output_list = output_list + ' ' + (f.get_text())
	
	return output_list

# Custom parsing subroutine for sections that have just title and body, supporting subsections
# that have their own subtitles.  This should work for most abstract / intro / discussion sections.	
def parse_title_body(root):
	subsections = root.find_all(attrs={'class': re.compile('^%s' % SUBSECTION_CLASS)})
	title = root.find(['strong','h2','h3','h4']).contents[0]
	output = collections.OrderedDict()
	logging.info('PARSING.... %s' % title)
	
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
			for d in c.contents:
				if isinstance(d, basestring):
					body += d
					body += ' '
		
		# Case when there are no subsections: output body as key to title
		output[title] = body
				
	return output
		
# Primary method for pulling each article.  Find the content sub-tree of the DOM, then use mini-parsers for each type of section
# NOTE: doesnt currently support generalized scraping of non-recognized article sections
def pull_article(root_link):
	try:
		content = collections.OrderedDict()
		soup = getsoup(root_link)
		article = soup.find_all('div',class_=CONTENT_CLASS)[0]
		# Find Keywords
		kwd = article.find_all(attrs={'class': re.compile(KEYWORD_CLASS)})
		if len(kwd) > 0:
			try:
				content['Key words'] = parse_keywords(kwd[0])['Key words']
				logging.info('Keywords parsed!')
			except:
				logging.info('ERROR parsing keywords')
				logging.exception("message")
		# Find section headers (children of full article div)	
		for s in article.find_all(attrs={'class': re.compile('^%s' % SECTION_PREFIX)}):
			try:
				section_type = s['class'][1]
				try:
					if section_type in TITLE_BODY_PARSABLE:
						output = parse_title_body(s)
						for key in output.keys():
							content[key] = output[key]
						logging.info('Parsed section: %s' % section_type)
					#elif section_type == KEYWORD_CLASS:
					#	content[section_type] = parse_keywords(s)
					#	logging.info('Parsed section: %s' % section_type)
					elif section_type == FOOTNOTE_CLASS:	
						content['Footnotes'] = parse_footnotes(s)
						logging.info('Parsed section: %s' % section_type)
					elif section_type == REFERENCE_CLASS:
						content['References'] = parse_references(s)['References']
						logging.info('Parsed section: %s' % section_type)
					else:
						logging.info('UNSUPPORTED SECTION: %s' % section_type)	
				except Exception as e:
					logging.info('ERROR parsing %s' % section_type)
					logging.exception("message")
			except:
				logging.info('Could not find section. Skipped.')	
	except:
		logging.info('Error loading article')
		logging.exception("message")
	return content

content = pull_article('http://circ.ahajournals.org/content/134/4/270.long')