from tqdm import tqdm
import re
import sys, os, csv
import codecs

currentPath = os.path.dirname(os.path.abspath(__file__)) + '/'
redirects_path='/media/sf_project/data/redirects_en.ttl'
index_path='/media/sf_project/data/redirects_en.txt'
index_filtered_path='/media/sf_project/data/redirects.csv'
relations_path = currentPath + '../data/mappingbased_objects_en_extracted.csv'
delimiter = '#'  # '#' is never used as character in page titles
totalLines = 7339092
limit = 1e12
REGEX = re.compile("<http://dbpedia.org/resource/(.*)> <.*> <http://dbpedia.org/resource/(.*)>.")

def dbpediaURLtoResource(url):
    # "http://dbpedia.org/resource/Allan_Dwan" --> "Allan Dwan"
    resource = url[28:]
    return resource

def unicode_csv_reader(utf8_data, dialect=csv.excel, **kwargs):
    csv_reader = csv.reader(utf8_data, dialect=dialect, **kwargs)
    for row in csv_reader:
        yield [unicode(cell, 'utf-8') for cell in row]

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

def filterTextIndex():
    with open(index_path, 'r') as fin_index, \
            open(relations_path, 'r') as fin_relations, \
            codecs.open(index_filtered_path, 'w', encoding="utf8") as fout:

        relationreader = csv.reader(fin_relations, delimiter=' ', quotechar='"')
        important_articles = set()

        print "Collecting important articles..."
        for line in tqdm(relationreader, total=500000):
        	#if "Cornelia" in dbpediaURLtoResource(line[2]):
        	#	print("ja")

        	important_articles.add(dbpediaURLtoResource(line[2]))

        print(len(important_articles))
        #for a in important_articles:
        	#print(a)
        print("Cornelia_de_Lange_syndrome".encode('utf-8') in important_articles)
        print(str("Stiles'_Tapaculo") in important_articles)
        indexreader = csv.reader(fin_index, delimiter=delimiter)
        # fout.write('"sep=' + delimiter + '"\n')
        print "Filtering important articles..."
        for line in tqdm(indexreader, total=7400000):
			#print(line[0])
			if line[0] in important_articles:
				fout.write(line[0] + delimiter + line[1] + '\n')
