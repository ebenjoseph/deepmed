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
outfile = open('Arduino_ES_output.jsonl', 'a')

# read in csv
with open('20160629-080248_loprovES_data.csv', 'rU') as csvfile:
	reader = csv.reader(csvfile, delimiter=',')
	counter = 0
	for row in reader:
		data = collections.OrderedDict()
		if not counter:
			counter += 1
			continue
		#data['run_id'] = row[0]
		data['time_retrieved'] = row[1]
		#data['time_end'] = row[2]
		data['capture_time'] = row[3]
		data['search_term'] = row[4]
		data['search_results'] = row[5]
		data['result_page'] = row[6]
		data['total_pages'] = row[7]
		data['result_number'] = row[8]
		data['pmid'] = row[9]
		data['title'] = row[10]
		data['authors'] = row[11]
		data['affiliations'] = row[12]
		data['journal_name'] = row[13]
		data['journal_code'] = row[14]
		data['pubtypes'] = row[15]
		data['meshterms'] = row[16]
		data['citation'] = row[17]
		data['pubdate'] = row[18]
		data['pubmed_page'] = row[19]
		data['link'] = row[20]

		journals_to_scrape.append(data)

counter = 0
docs = []
##												 		##
##  UPDATE ARTICLE CHECKING FILENAME WITH EACH LIBRARY  ##
##												 		##
articletracker = 'Arduino_ES_article_tracker'

p = re.compile(ur'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', re.MULTILINE)
sub = u"\n\n"
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
logging.basicConfig(filename='scraping_log.log',level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
streamthelog = logging.StreamHandler(sys.stdout)
streamthelog.setLevel(logging.INFO)
streamthelog.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p'))
root.addHandler(streamthelog)

def getsoup(root_link):
	try:
		session = requests.Session()
		session.headers = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/600.8.9 (KHTML, like Gecko) Version/8.0.8 Safari/600.8.9'
		#run locally on the arduino, use this:################################################
		#web_page = session.get(root_link)
		#with deepmed proxy for aws, use these:###############################################
		proxies = {
		    "http": "http://deepmed:deepmed@10.254.18.174:3128",
		}
		web_page = session.get(root_link, proxies=proxies)
	except:
		logging.info('Error requesting page...')
		return -1
	sleep(2)
	#return BeautifulSoup(web_page.content, "html.parser") #python's parser
	return BeautifulSoup(web_page.content, "lxml") #lxml (faster)

def get_name(sibs):
	try:
		return str(sibs.name)
	except:
		return 'None'

def grab_text(sibs):
	try:
		return sibs.get_text().encode("utf-8")
	except:
		return ''

def check_subheader(subheader,sibs):
	try:
		strong = get_name(sibs.contents[0])
	except:
		strong = ''
	if get_name(sibs) == 'h4':
		#found h4, set as new subheader
		subheader = grab_text(sibs)
	if get_name(sibs) == 'h3':
		#found h3, set as new subheader
		subheader = grab_text(sibs)
	if get_name(sibs) == 'h2':
		#found h2, set as new subheader
		subheader = grab_text(sibs)
	if strong == 'strong':
		#found strong, set as new subheader
		subheader = grab_text(sibs.contents[0])
	return subheader

def check_attrib(sibs, attrib):
	try:
		sibid = sibs[attrib]
		return sibid
	except:
		return 'Not found'

def check_objtype(sibs):
	try:
		strong = get_name(sibs.contents[0])
	except:
		strong = ''
	if (get_name(sibs) == 'ol'):
		#found the references list
		objtype = "references"
	elif 'artFooterContent' in check_attrib(sibs,'class'): 
		#found the footer
		objtype = "footer"
	elif get_name(sibs) == 'h4':
		#found a header
		objtype = "header"
	elif get_name(sibs) == 'h3':
		#found a header
		objtype = "header"
	elif get_name(sibs) == 'h2':
		#found a header
		objtype = "header"
	elif strong == 'strong':
		#found a header
		objtype = "header"
	elif 'table' in check_attrib(sibs,'id'): 
		#found a table
		objtype = "table"
	else:
		objtype = "data"
	#print objtype   #################
	#sleep(1)        #################
	#print "" 		#################
	return objtype

def grabtable(sibs):
	try:
		#Grab the title of the table
		titleobj = sibs.find_all('div',class_='caption')
		header = ""
		title = ""
		for note in titleobj:
			title = title + " " + grab_text(note)
		legendobj = sibs.find_all('p',class_='legend')
		legend = ""
		for note in legendobj:
			legend = legend + " " + grab_text(note.next_sibling)
		footnoteobj = sibs.find_all('dl',class_='tblFootnote')
		footnote = ""
		for note in footnoteobj:
			footnote = footnote + " " + grab_text(note)
		#get table headers
		try:
			th = []
			tablehead = sibs.find('thead')
			if not get_name(tablehead) == 'None':
				all_trth = tablehead.find_all('tr')
				if len(all_trth) == 2:
					all_th = all_trth[0].find_all('th')
					for each in all_th:
						#print check_attrib(each,'colspan')
						cols = int(check_attrib(each,'colspan'))
						if cols > 1:
							thheader = grab_text(each)
							all_th2 = all_trth[1].find_all('th')
							for each in all_th2:
								th.append(thheader + ", " + grab_text(each))
						else:
							th.append(grab_text(each))
				elif len(all_trth) > 2:
					all_th = all_trth[0].find_all('th')
					for each in all_th:
						#print check_attrib(each,'colspan')
						cols = int(check_attrib(each,'colspan'))
						if cols > 1:
							thheader = grab_text(each)
							all_th2 = all_trth[1].find_all('th')
							for each in all_th2:
								#print check_attrib(each,'colspan')
								cols = int(check_attrib(each,'colspan'))
								if cols > 1:
									thheader2 = grab_text(each)
									all_th3 = all_trth[2].find_all('th')
									for each in all_th3:
										th.append(thheader + ", " + thheader2 + ", " + grab_text(each))
								else:
									th.append(thheader + ", " + grab_text(each))
						else:
							th.append(grab_text(each))
				else:
					all_th = tablehead.find_all('th')
					for each in all_th:
						#print check_attrib(each,'colspan')
						cols = int(check_attrib(each,'colspan'))
						colcounter = 0
						#print colcounter
						while colcounter < cols:
							colcounter += 1
							th.append(grab_text(each))
							#print colcounter
							#print grab_text(each)
				tablecontent = []
				#get all rows
				rows = sibs.find_all('tr')
				for tr in rows:
					cells = tr.find_all('td')
					idx = -1
					rowheader = ""
					for cell in cells:
						idx += 1
						if rowheader == "":
							#rowheader is blank and we still need to find it
							rowheader = grab_text(cell)
						cols = int(cell['colspan'])
						if cols == len(th):
							#this is a header row
							header = grab_text(cell)
							#print "Found a header row"
							#print header
						if cols == 2:
							idx += 1
							if not rowheader == "":
								#this row has a rowheader, so turn off the previous header
								header = ""
							if rowheader == "":
								#skip printing
								#not a row header and cell is blank, so it is a spacer: previous rowheader is meta-header
								continue
							elif rowheader == grab_text(cell):
								#just found rowheader, skip printing
								continue
							if not header == "":
								tablecontent.append(th[idx-1] + ", " + th[idx] + "; " + header + " - " + rowheader + ": " + grab_text(cell))
							else:
								tablecontent.append(th[idx-1] + ", " + th[idx] + "; " + rowheader + ": " + grab_text(cell))
						else:
							if rowheader =="":
								#skip printing
								continue
							elif rowheader == grab_text(cell):
								#just found rowheader, skip printing
								continue		
							if not header == "":
								tablecontent.append(th[idx] + "; " + header + " - " + rowheader + ": " + grab_text(cell))
							else:
								tablecontent.append(th[idx] + "; " + rowheader + ": " + grab_text(cell))
			else:
				tablecontent = []
				#get all rows
				rows = sibs.find_all('tr')
				for tr in rows:
					cells = tr.find_all('td')
					for cell in cells:
						tablecontent.append(grab_text(cell))
		except:
			tablecontent = 'N/A'
		table = {}
		table["Title"] = title
		table["Content"] = tablecontent
		table["Footnote"] = footnote
		table["Legend"] = legend
		return table
	except:
		table = {}
		return table

def pull_journal(journal):
	root_link = journal['link']

	if not len(journalsRead) % 10: print len(journalsRead)
	
	journalLock.acquire()

	#print len(journalsRead)
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
	
	articledata = {}
	fullarticle = ""

	
	'''
	SAMPLE LINKS FROM THE ES DATASET:
	http://www.ncbi.nlm.nih.gov/pubmed/?term=%22loprovES%22%5BFilter%5D%20AND%20%22loattrfull%20text%22%5Bsb%5D%20AND%20English%5Blang%5D%20AND%20%22humans%22%5BFilter%5D%20AND%20%22Clinical%20Trial%22%5Bptyp%5D&cmd=DetailsSearch

	http://www.sciencedirect.com/science/article/pii/S0140673616005572
	http://www.sciencedirect.com/science/article/pii/S0140673616300691
	http://www.sciencedirect.com/science/article/pii/S0140673616303105?np=y
	http://www.sciencedirect.com/science/article/pii/S0140673616303105?np=y
	'''
	try:
		#specific to ES: link requires '?np=y' appended to end in order to not use javascript
		#root_link = "http://linkinghub.elsevier.com/retrieve/pii/S0022-4804(15)00809-4"
		#root_link = "http://www.sciencedirect.com/science/article/pii/S0140673616303105?np=y"
		#root_link = "http://www.sciencedirect.com/science/article/pii/S0161642014008616?np=y"
		#root_link = "http://www.sciencedirect.com/science/article/pii/S0090429514009728?np=y"
		#root_link = "http://www.sciencedirect.com/science/article/pii/S0002870315006274?np=y"
		root_link = root_link.replace("(","")
		root_link = root_link.replace(")","")
		root_link = root_link.replace("-","")
		root_link = root_link.replace("http://linkinghub.elsevier.com/retrieve/","http://www.sciencedirect.com/science/article/")
		root_link = root_link + '?np=y'

		soup = getsoup(root_link)
		logging.info("Article loaded...")

		#Full article text from Title through references
		article_text = grab_text(soup.find('div',id='centerInner'))

		# if fullarticle length is < 4000 characters, it's probably junk, so don't add
		if len(article_text) < 4000: 
			print 'Short article (less than 4,000 chars) - not adding'
			return
		logging.info('Article longer than 4,000 chars -- attempting to parse...')
		article = soup.find('div',id='centerInner')
		content = collections.OrderedDict()
		logging.info('Starting parse loop...')
		try:
			abst = article.find('div',class_='svAbstract')
			try:
				main = abst.find_all('h2',class_='secHeading')
				main = main + abst.find_all(id=lambda x: x and (x.startswith('spara') or x.startswith('abs')))
				main = main + article.find_all(attrs={'class':['svArticle','references','svKeywords','artFooterContent']})
			except:
				main = main + abst.find_all(id=lambda x: x and (x.startswith('spara') or x.startswith('abs')))
				main = main + article.find_all(attrs={'class':['svArticle','references','svKeywords','artFooterContent']})
		except:
			main = article.find_all(attrs={'class':['svArticle','references','svKeywords','artFooterContent']})

		header = "Header"
		subheader = ""
		content[header] = ""
		for sibs in main:
			#print sibs ########################
			logging.info('     Header: %s', header)
			if get_name(sibs) == 'h2':
				header = grab_text(sibs)
				#print header + "------------------------" #######################
				subheader = ""
				continue
			#check header status
			subheader = check_subheader(subheader,sibs)
			#check type of obj
			objtype = check_objtype(sibs)
			if objtype == 'footer':
				header = 'Footer'
				subheader = ''
				key = header
				temp = str(content.get(key,"")) + " " + grab_text(sibs)
				content[key] = temp
				continue
			if objtype == 'header':
				#this is a header and we don't want to add it to the content
				logging.info('     Subheader: %s', subheader)
				key = header + ": " + subheader
				content[key] = ""
				continue
			if objtype == 'table':
				#this is a table, we need to add it to the table dicts
				table = grabtable(sibs)
				table["Section"] = header
				content["Tables"] = content.get("Tables", []) + [table]
				continue
			if objtype == 'references':
				#this is the reference list, we need to split it into a list and add it to the references header
				ref = []
				bibs = sibs.find_all('li',id=lambda x: x and (x.startswith('bib') or (x.startswith('bb'))))
				for item in bibs:
					if not grab_text(item) == '':
						ref = ref + [grab_text(item)]
				continue
			if objtype == 'data':
				#print "adding data to " + header
				#We found some data, we need to add it to the right dictionary
				#either there is no subheader:
				if subheader == '':
					#add to the header dictionary under content key
					key = header
					#temp = str(content[key]) + " " + grab_text(sibs)
					temp = str(content.get(key,"")) + " " + grab_text(sibs)
					content[key] = temp
					continue
				#or there is a subheader:
				else:
					#add to the header dictionary under a subheader dict
					key = header + ": " + subheader
					#temp = str(content[key]) + " " + grab_text(sibs) 
					temp = str(content.get(key,"")) + " " + grab_text(sibs) 
					content[key] = temp
				continue

		#Reference section may have text in addition to citations, so add the refs list, then append any text to the end of the list
		content["References"] = ref + [content.get("References","")]
		logging.info('Article successfully parsed!')

		#Abstract section
		#References section
		#item listing includes any svArticle items
		#starts with Abstract, then header, then content + tables, then ends with References

		#pass through webscraped metadata
		data['time_retrieved'] = journal['time_retrieved']
		data['capture_time'] = journal['capture_time']
		data['search_term'] = journal['search_term']
		data['search_results'] = journal['search_results']
		data['result_page'] = journal['result_page']
		data['total_pages'] = journal['total_pages']
		data['result_number'] = journal['result_number']
		data['pmid'] = journal['pmid']
		data['title'] = journal['title']
		data['authors'] = journal['authors']
		data['affiliations'] = journal['affiliations']
		data['journal_name'] = journal['journal_name']
		data['journal_code'] = journal['journal_code']
		data['pubtypes'] = journal['pubtypes']
		data['meshterms'] = journal['meshterms']
		data['citation'] = journal['citation']
		data['pubdate'] = journal['pubdate']
		data['pubmed_page'] = journal['pubmed_page']
		data['link'] = journal['link']

		#new data pulled from article link
		data['golden'] = 0
		data['content'] = content
		logging.info("Article added!")

		writingLock.acquire()
		json.dump(data, outfile)
		outfile.write('\n')
		writingLock.release()

		return 1

	except:
		logging.info("Error! Could not parse or could not output to JSON")
		logging.info(root_link)
		return

logging.info("Scraper started at " + str(datetime.now()) )
# setup threadpool
pool = ThreadPool(16)

results = pool.map(pull_journal, journals_to_scrape)

pool.close()
pool.join()
	
# output results
print len(results)

logging.info("Run finished. Processed %s articles.", len(results))
outfile.close()
journalfile.close()

