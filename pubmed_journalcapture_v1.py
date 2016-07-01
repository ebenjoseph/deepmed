#Uses FullLinkText from the PubMed harvester to capture full text from the provided links

#Set up generally accepted headers for request
hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}

#read in csv, save all variables

#test links
'''
http://www.ncbi.nlm.nih.gov/pmc/articles/pmid/27178424/
http://bmccancer.biomedcentral.com/articles/10.1186/s12885-016-2347-5
'''

import lxml.html

url = "http://www.ncbi.nlm.nih.gov/pmc/articles/pmid/27178424/"
tree = lxml.html.parse(url)
listings = tree.xpath('//')
print listings

#output to JSON file with PMID, Citation, Journal, JournalCode, FullTextLink, and FullText





#Requirements:
from lxml import html
import requests
import tldextract

#grab fulltextlink to capture
input_url = 'http://www.ncbi.nlm.nih.gov/pmc/articles/pmid/27178424/'

#Grab the url, watch for redirects, and parse the html
response = requests.get(input_url)
capture_url = response.status_code, response.url
url = capture_url[-1]
parsed_body = html.fromstring(response.text.encode("utf-8"))

#convert input url to domain
ext = tldextract.extract(url)
domain = '.'.join(ext)

if (domain == 'www.ncbi.nlm.nih.gov'):
	path = '//div[@id="maincontent"]//text()' #http://www.ncbi.nlm.nih.gov/pmc/articles/PMC4868009/

fulltext = "".join(parsed_body.xpath(path))
print fulltext

url = 'http://forums.bbc.co.uk'
url = 'http://www.ncbi.nlm.nih.gov/pmc/articles/pmid/27178424/'
ext = tldextract.extract(url)
ext.domain





#inputurl
#redirecturl



###
# [think about how to pool, pull, and mutlithread these requests]
# Load the page
# Check the URL after it has loaded
# trim down to the subdomain
# use assigned subdomain filter
# if no match is found, apply all the filters, if one matches, then make a note for review
# 


"heart"[All Fields] AND "loprovPMC"[Filter] AND "loattrfull text"[sb]
"loprovPMC"[Filter] AND "loattrfull text"[sb]
#Libraries
AND "loprovPMC"[Filter] #PMC
AND "loprovOvid"[Filter] #Ovid
AND "loprovWiley"[Filter]  #wiley
AND "loprovES"[Filter]  #elsevier
AND "loprovHighWire"[Filter] #highwire
AND "loprovSpringer"[Filter] #springer
AND "loprovNPG"[Filter]  #nature publishing group

















