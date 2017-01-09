import xml.etree.ElementTree as etree
from bs4 import BeautifulSoup as bs
from tqdm import tqdm
import csv
import os
import operator
from timeit import default_timer as timer

currentPath = os.path.dirname(os.path.abspath(__file__)) + '\\'
pathDump = 'D:\\Data\\large\\enwiki-latest-pages-articles.xml'
pathIndex = 'D:\\Data\\large\\character_index.csv'
pathIndexSorted = 'D:\\Data\\large\\character_index_sorted.csv'
pathIndexFiltered = 'D:\\Data\\large\\character_index_filtered.csv'
pathRelations = currentPath + '..\\ttl parser\\mappingbased_objects_en_extracted.csv'  # TODO: change to mappingbased_objects_en.tll and adjust code
limit = 1e12
delimiter = '#'  # '#' is never used as character in page titles


def _make_gen(reader):
    b = reader(1024 * 1024)
    while b:
        yield b
        b = reader(1024 * 1024)


def rawpycount(filename):
    # http://stackoverflow.com/questions/19001402/how-to-count-the-total-number-of-lines-in-a-text-file-using-python
    print "Counting Lines..."
    f = open(filename, 'rb')
    f_gen = _make_gen(f.read)
    return sum(buf.count(b'\n') for buf in f_gen)


def parseXML():
    # path = 'D:\Data\large\head.xml'
    # tree = etree.parse(path)
    # root = tree.getroot()

    prefix = '{http://www.mediawiki.org/xml/export-0.10/}'
    pageTag = prefix + 'page'
    titleTag = prefix + 'title'
    revisionTag = prefix + 'revision'
    textTag = prefix + 'text'

    # print root.find('{http://www.mediawiki.org/xml/export-0.10/}page')

    # for child in root.findall(pageTag):
    # title = child.find(titleTag).text
    # print title
    # text = child.find(revisionTag).find(textTag).text
    # print title, text

    counter = 0
    searchTitle = 'Alan Turing'
    for event, elem in etree.iterparse(path, events=('start', 'end', 'start-ns', 'end-ns')):
        if event == 'end' and elem.tag == pageTag:
            title = elem.find(titleTag).text
            # print title
            if title == searchTitle:
                text = elem.find(revisionTag).find(textTag).text
                print title
                print text
                print counter
                break
            incrementCounter()
            limit -= 1
            if limit == 0:
                break
            elem.clear()

            # soup = bs(open(path), 'lxml')
            # text = soup.find_all('page')
            # print text


def createTextIndex():
    totalLines = 930000000  # rawpycount(pathInput) # TODO: replace magic number with line counter
    with open(pathDump, 'r') as fin, open(pathIndex, 'w') as fout:
        lineCounter = 0
        characterOffset = 0
        pageFound = False

        fout.write('"sep=' + delimiter + '"\n')

        tqdm.write('\n\nCreating index...')
        for line in tqdm(fin, total=totalLines):
            if pageFound:
                pageFound = False
                title = line[11:-9]
                fout.write(title + delimiter + str(characterOffset) + '\n')

            if line[0:8] == "  <page>":
                pageFound = True

            characterOffset += len(line)
            lineCounter += 1
            if lineCounter == limit:
                break
        fin.close()
        fout.close()


def extractPageFromOffset(offset):
    with open(pathDump, 'r') as fin:
        fin.seek(offset)
        text = "  <page>\n"
        for line in fin:
            text += line
            if line[0:9] == "  </page>":
                break
        return text


def extractPage(title):
    with open(pathIndexSorted, 'r') as fin:
        indexreader = csv.reader(fin, delimiter=delimiter)
        for line in indexreader:
            if line[0] == title:
                return extractPageFromOffset(int(line[1]))
        fin.close()
    print "No page found named: " + title


def sortIndex():
    """ for index lookup in O(log i) instead of O(i) with i as the size of the index """
    with open(pathIndexFiltered, 'r') as fin, open(pathIndexSorted, 'w') as fout:
        indexreader = csv.reader(fin, delimiter=delimiter)
        sortedList = sorted(indexreader, key=operator.itemgetter(0))
        fout.write('"sep=' + delimiter + '"\n')
        totalLines = rawpycount(pathIndex)
        tqdm.write('\n\nSorting index...')
        for element in tqdm(sortedList, total=totalLines):
            fout.write(element[0] + delimiter + element[1] + '\n')


def dbpediaURLtoResource(url):
    # "http://dbpedia.org/resource/Allan_Dwan" --> "Allan Dwan"
    resource = url[28:]
    resource = resource.replace('_', ' ')
    return resource


def createFilteredIndex():
    with open(pathIndex, 'r') as fin_index, \
            open(pathRelations, 'r') as fin_relations, \
            open(pathIndexFiltered, 'w') as fout:

        relationreader = csv.reader(fin_relations, delimiter=' ', quotechar='"')
        important_articles = set()
        totalLines = rawpycount(pathRelations)
        tqdm.write('\n\nCollecting important articles...')
        for line in tqdm(relationreader, total=totalLines):
            important_articles.add(dbpediaURLtoResource(line[0]))

        indexreader = csv.reader(fin_index, delimiter=delimiter)
        totalLines = rawpycount(pathIndex)
        # fout.write('"sep=' + delimiter + '"\n')
        tqdm.write('\n\nFiltering importatnt articles...')
        for line in tqdm(indexreader, total=totalLines):
            if line[0] in important_articles:
                fout.write(line[0] + delimiter + line[1] + '\n')


def extractText(page):
    root = etree.fromstring(page)
    text = root.find('revision').find('text').text
    return text


if __name__ == '__main__':
    # parseXML()
    # createTextIndex()
    # createFilteredIndex()
    # sortIndex()

    start = timer()
    page = extractPage('Albert Einstein')  # TODO: Heed also names with non-ascii characters
    end = timer()
    print "Elapsed time:", str(end - start), "seconds"

    print extractText(page)
