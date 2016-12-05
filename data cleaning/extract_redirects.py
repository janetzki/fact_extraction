from tqdm import tqdm
import re
import sys, os, csv

redirects_path='../data/redirects_en.ttl'
index_path='../data/redirects_en.txt'
delimiter = '#'  # '#' is never used as character in page titles
totalLines = 7339092
limit = 1e12
REGEX = re.compile("<http://dbpedia.org/resource/(.*)> <.*> <http://dbpedia.org/resource/(.*)>.")

def parseTTL(input):
	match = REGEX.match(input)
	if match:
		return match.group(1), match.group(2)
	else: 
		return False, False

def createTextIndex():
	with open(redirects_path, 'r', encoding="UTF-8") as fin, open(index_path, 'w', encoding="UTF-8") as fout:
		lineCounter = 0
		characterOffset = 0

		fout.write('"sep=' + delimiter + '"\n')

		for line in tqdm(fin, total=totalLines):
			name, ressource = parseTTL(line)
		
			if name:
				fout.write(name + delimiter + ressource + '\n')

			characterOffset += len(line)
			lineCounter += 1
			if lineCounter == limit:
				break
		fin.close()
		fout.close()