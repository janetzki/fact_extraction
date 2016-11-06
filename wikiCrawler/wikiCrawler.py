import csv
import urllib.request as urlreq
import urllib.parse
import xml.etree.ElementTree as ET
import sys
import codecs
import re

sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

fileName = 'mappingbased_objects_en_extracted_full.csv'
articles = {}
i = int(sys.argv[2])
property = sys.argv[1]

def segmentate(text):
	rows = text.split("\n")
	segments = []
	for row in rows:
		if(row) != "":
			segments = segments + row.split(".")
		
	return segments

with open(fileName, 'r', encoding='utf-8-sig') as csvfile:
	wikireader = csv.reader(csvfile, delimiter=' ', quotechar='"')
	for row in wikireader:
		if(i == 0):
			break
		if(row[1].find(property) == -1):
			continue
		if row[0] in articles:
			content = articles[row[0]]
		else:
			i = i - 1
			
			url = urllib.parse.urlsplit(row[0])
			url = list(url)
			url[2] = urllib.parse.quote(url[2])
			url = urllib.parse.urlunsplit(url)
			url = url.replace("dbpedia.org/resource", "en.wikipedia.org/wiki")
			print(url)
			html = urlreq.urlopen(url).read()

			html = html.replace(b"&nbsp;", b"&#0160;")
			root = ET.fromstring(html)
			content = root.findall(".//div[@id='mw-content-text']")[0]
			
			articles[row[0]] = content
		
		prop = row[2].replace("http://dbpedia.org/resource", "/wiki")
		entity = prop.replace("/wiki/", "")
		
		
		searchStr = []
		searchStr.append(entity.replace("_", " "))
		for anker in content.findall('.//a[@href="' + prop + '"]'):
			link_text = "".join(anker.itertext())	
			if not link_text in searchStr:
				searchStr.append(link_text)
	
		text = "".join(content.itertext())
		#print(text)
		
		sentences = segmentate(text)
		print(len(sentences), "sentences")
		print(searchStr)

		for sentence in sentences:
			#print(sentence)
			for search in searchStr:
				if(sentence == search): continue
				pos = sentence.find(search)
				if(pos > -1):
					print("1", sentence[:pos])
					print("2", search)
					last = len(search) + pos
					print("3", sentence[last:])
					print("")