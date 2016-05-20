# comment

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

journals_to_scrape = []
outfile = open('output_test.jsonl', 'a')

# read in csv
with open('testing.csv', 'rU') as csvfile:
	reader = csv.reader(csvfile, delimiter=',')
	counter = 0
	for row in reader:
		data = {}
		if not counter:
			counter += 1
			continue

		data['journal'] = row[5]
		data['id'] = row[8]
		data['link'] = row[9]
		journals_to_scrape.append(data)


'''links_to_scrape = [
'http://dx.doi.org/10.1111/j.1532-5415.2011.03391.x',
'http://linkinghub.elsevier.com/retrieve/pii/S0735-1097(04)01219-7',
'http://www.ima.org.il/IMAJ/ViewArticle.aspx?year=2010&month=08&page=489',
'http://eurheartj.oxfordjournals.org/cgi/pmidlookup?view=long&pmid=16717081',
'http://linkinghub.elsevier.com/retrieve/pii/S0002934302014985',
'http://linkinghub.elsevier.com/retrieve/pii/S0735-1097(00)00613-6',
'http://www.nejm.org/doi/abs/10.1056/NEJMoa1214865?url_ver=Z39.88-2003&rfr_id=ori:rid:crossref.org&rfr_dat=cr_pub%3dwww.ncbi.nlm.nih.gov',
'http://linkinghub.elsevier.com/retrieve/pii/S0002-8703(13)00158-0',
'http://www.annals.org/article.aspx?doi=10.7326/0003-4819-153-3-201008030-00010',
'http://linkinghub.elsevier.com/retrieve/pii/S0002961097000731',
'http://onlinelibrary.wiley.com/resolve/openurl?genre=article&sid=nlm:pubmed&issn=0041-1132&date=1998&volume=38&issue=6&spage=522',
'http://www.nejm.org/doi/abs/10.1056/NEJMoa1012452?url_ver=Z39.88-2003&rfr_id=ori:rid:crossref.org&rfr_dat=cr_pub%3dwww.ncbi.nlm.nih.gov',
'http://meta.wkhealth.com/pt/pt-core/template-journal/lwwgateway/media/landingpage.htm?issn=0090-3493&volume=29&issue=2&spage=227',
'http://linkinghub.elsevier.com/retrieve/pii/S0002-9149(11)02003-0',
'http://linkinghub.elsevier.com/retrieve/pii/S0002-9149(11)02003-0'
]'''

counter = 0
docs = []
p = re.compile(ur'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', re.MULTILINE)
sub = u"\n\n"
journalsRead = {}

# read in previously read journal links
journalfile = open('journals', 'r')
for line in journalfile:
	journalsRead[line.rstrip()] = 1

journalfile.close()
journalfile = open('journals', 'a')

journalLock = threading.Lock()
writingLock = threading.Lock()

# setup logging
logging.basicConfig(filename='scraping_log.log',level=logging.DEBUG)
logging.info("Scraper started " + str(datetime.now()) )

def getsoup(root_link):
	try:
		web_page = requests.get(root_link)
	except:
		logging.info('error parsing initial page')
		return -1
	sleep(3)
	return BeautifulSoup(web_page.content, "html.parser")

def remove_tags(text):
  return ''.join(xml.etree.ElementTree.fromstring(text).itertext())

def pull_journal(journal):
	root_link = journal['link']

	#if not len(journalsRead) % 10: print len(journalsRead)
	journalLock.acquire()
	print len(journalsRead)

	try:
		journalsRead[root_link]
		journalLock.release()
		print 'skipping'
		return
	except:
		journalsRead[root_link] = 1

	journalLock.release()
	
	data = {}
	fullarticle = ""

	try:
		if root_link.find('www.nejm.org') > 0:
			data['journal'] = 'nejm'
			logging.info('nejm')
			soup = getsoup(root_link)		
			article = soup.find('dt', id='articleTab')
			try:
				fullpage = requests.get('http://www.nejm.org'+article.find('a').get('href').encode())
			except:
				logging.info('error parsing full article page')
				return
			sleep(3)

			articlesoup = BeautifulSoup(fullpage.content, "html.parser")
			fullarticle = str(articlesoup.find('dd', id='article'))
		
		elif root_link.find('elsevier') > 0:
			data['journal'] = 'elsevier'
			logging.info('elsevier')
			soup = getsoup(root_link)
			fullarticle = str(soup.find('div', id='centerInner'))
		
		elif root_link.find('jama') > 0:
			data['journal'] = 'jama'
			logging.info('jama')
			soup = getsoup(root_link)
			fullarticle = str(soup.find('div', id='tab1'))
		
		elif root_link.find('ahajournals') > 0:
			data['journal'] = 'ahajournals'
			soup = getsoup(root_link)
			fullarticle = str(soup.find('div', itemprop='articleBody'))
		
		elif root_link.find('nlm.nih') > 0:
			data['journal'] = 'nih'
			logging.info('nih')
			soup = getsoup(root_link)
			fullarticle = str(soup.find('div', class_='body-content whole_rhythm'))
		
		elif root_link.find('http://aac.asm.org/') > 0:
			data['journal'] = 'asm'
			logging.info('asm')
			soup = getsoup(root_link)
			fullarticle = str(soup.find('div', itemprop='articleBody'))

		elif root_link.find('dx.doi.org/10.1155/') > 0:
			data['journal'] = 'Biomed Res Int + others'
			soup = getsoup(root_link)
			fullarticle = str(soup.find('h4', class_='header').parent)

		elif root_link.find('dx.doi.org/10.1002/uog') > 0:
			data['journal'] = '/10.1002/uog'
			soup = getsoup(root_link)
			fullArticleLink = soup.find('div', class_='accordion__title')

			try:
				fullpage = requests.get(fullArticleLink.find('a').get('href').encode())
			except:
				print 'error pulling full article link'
				return
			sleep(3)

			fullArticleSoup = BeautifulSoup(fullpage.content, "html.parser")
			fullarticle = str(fullArticleSoup.find('article', class_='issue'))

		elif root_link.find('dx.doi.org/10.1002/anie') > 0:
			data['journal'] = '/10.1002/anie'
			soup = getsoup(root_link)
			
			fullArticleLink = soup.find('div', class_='accordion__title')

			try:
				fullpage = requests.get(fullArticleLink.find('a').get('href').encode())
			except:
				print 'error pulling full article link'
				return
			sleep(3)

			fullArticleSoup = BeautifulSoup(fullpage.content, "html.parser")
			fullarticle = str(fullArticleSoup.find('article', class_='issue'))

		elif root_link.find('dx.doi') > 0:
			data['journal'] = 'dxdoi'
			logging.info('dxdoi')
			soup = getsoup(root_link)
			article = soup.find('div', class_='tabbedContent')
			try:
				article = article.find_all('a')[0].get('href').encode()
			except:
				return

			try:
				fullpage = requests.get('http://onlinelibrary.wiley.com'+article)
			except:
				logging.info('error parsing full article page')
				return
			sleep(3)
			articlesoup = BeautifulSoup(fullpage.content, "html.parser")
			fullarticle = str(articlesoup.find('div', id='fulltext'))

		elif root_link.find('dx.plos.org') > 0:
			data['journal'] = 'plos'
			soup = getsoup(root_link)
			fullarticle = str(soup.find('div', id='artText'))

		elif root_link.find('eurheartj.oxfordjournals.org/') > 0:
			data['journal'] = 'Eur Heart J'
			soup = getsoup(root_link)
			fullarticle = str(soup.find('div', class_='panel-panel panel-region-content panel-bottom-margin large-padding block-section'))

		elif root_link.find('aac.asm.org') > 0:
			data['journal'] = 'aac-asm'
			soup = getsoup(root_link)
			fullarticle = str(soup.find('div', itemprop='articleBody'))

		elif root_link.find('thij.org') > 0:
			data['journal'] = 'Tex Heart Inst J'
			soup = getsoup(root_link)		
			fullarticle = str(soup.find('div', id='articleContent'))

		elif root_link.find('oxfordjournals') > 0:
			data['journal'] = 'oxfordjournals'
			soup = getsoup(root_link)
			fullarticle = str(soup.find('div', itemprop='articleBody'))

		elif root_link.find('wjgnet') > 0:
			data['journal'] = 'WJG'
			soup = getsoup(root_link)
			fullarticle = str(soup.find('div', id='fulltext'))

		elif root_link.find('bmcinfectdis') > 0:
			data['journal'] = 'BMC Infect'
			soup = getsoup(root_link)
			fullarticle = str(soup.find('div', id='Test-ImgSrc'))

		elif root_link.find('pediatrics.aappublications') > 0:
			data['journal'] = 'pediatrics'
			soup = getsoup(root_link)
			fullarticle = str(soup.find('div', class_='highwire-markup'))

		elif root_link.find('bmjopen.bmj') > 0:
			data['journal'] = 'bmj'
			soup = getsoup(root_link)
			fullarticle = str(soup.find('div', itemprop='articleBody'))

		elif root_link.find('europace.oxfordjournals') > 0:
			data['journal'] = 'pediatrics'
			soup = getsoup(root_link)
			fullarticle = str(soup.find('div', class_='highwire-markup'))

		elif root_link.find('ccforum.biomedcentral') > 0:
			data['journal'] = 'biomedcentral'
			soup = getsoup(root_link)
			fullarticle = str(soup.find('div', id='Test-ImgSrc'))

		elif root_link.find('pnas') > 0:
			data['journal'] = 'pnas'
			soup = getsoup(root_link)
			fullarticle = str(soup.find('div', itemprop='articleBody'))

		elif root_link.find('/srep') > 0:
			data['journal'] = 'SciRep'
			soup = getsoup(root_link)
			fullarticle = str(soup.find('div', class_='article-body'))

		# final catch-all attempt
		else:
			try:
				data['journal'] = journal['journal']
				soup = getsoup(root_link)
				fullarticle = str(soup.find('div', itemprop='articleBody'))
			except:
				return


		try:
			clean = remove_tags(fullarticle)
			clean = ' '.join(clean.split())
		except:
			clean = re.sub('<[^<]+?>', '', fullarticle.decode('utf-8'))  #fullarticle.decode('utf-8')
			clean = ' '.join(clean.split())

		# if fullarticle length is < 2000 characters, it's probably junk, so don't add
		if len(fullarticle) < 2000: return

		data['id'] = journal['id']
		data['golden'] = 0
		data['content'] = re.sub(p, sub, clean)
		#print data
		#print '\n\n\n'

		writingLock.acquire()
		json.dump(data, outfile)
		outfile.write('\n')
		writingLock.release()

		return 1

	except:
		return


# setup threadpool
pool = ThreadPool(4)

results = pool.map(pull_journal, journals_to_scrape)

pool.close()
pool.join()
	
# output results
print len(results)

for key in journalsRead:
	journalfile.write(key)
	journalfile.write('\n')

outfile.close()
journalfile.close()

