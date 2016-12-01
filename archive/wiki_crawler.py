import csv
import urllib.request as urlreq
import urllib.parse
import xml.etree.ElementTree as ET
import sys
import codecs
import re
from termcolor import colored

# consoleRed = '\x1b[6;30;41m'
# consoleGreen = '\x1b[6;30;42m'
# consoleNormal = '\x1b[0m'

if __name__ == "__main__":
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

    fileName = '../ttl parser/mappingbased_objects_en_extracted.csv'
    articles = {}
    if (len(sys.argv) != 3):
        print("usage:   python wikiCrawler.py [property] [maxResults]")
        print("example: python wikiCrawler.py almaMater 100")
        exit()
    property = sys.argv[1]
    maxResults = int(sys.argv[2])


def segment(text):
    rows = text.split("\n")
    segments = []
    for row in rows:
        if (row) != "":
            segments = segments + row.split(".")

    return segments


def extractContent(url):
    url = list(url)
    url[2] = urllib.parse.quote(url[2])
    url = urllib.parse.urlunsplit(url)
    url = url.replace("dbpedia.org/resource", "en.wikipedia.org/wiki")
    print(colored(url, 'red'))
    html = urlreq.urlopen(url).read()

    html = html.replace(b"&nbsp;", b"&#0160;")
    root = ET.fromstring(html)
    content = root.findall(".//div[@id='mw-content-text']")[0]
    return content


with open(fileName, 'r', encoding='utf-8-sig') as csvfile:
    wikireader = csv.reader(csvfile, delimiter=' ', quotechar='"')
    for row in wikireader:
        subject = row[0]
        relation = row[1]
        value = row[2]
        print(colored(subject + ' ' + relation + ' ' + value, 'blue'))

        if (maxResults == 0):
            break
        if (relation.find(property) == -1):
            continue
        if subject in articles:
            content = articles[subject]
        else:
            maxResults -= 1
            url = urllib.parse.urlsplit(subject)
            content = extractContent(url)
            articles[subject] = content

        prop = value.replace("http://dbpedia.org/resource", "/wiki")
        entity = prop.replace("/wiki/", "")

        searchStr = []
        searchStr.append(entity.replace("_", " "))
        for anker in content.findall('.//a[@href="' + prop + '"]'):
            link_text = "".join(anker.itertext())
            if not link_text in searchStr:
                searchStr.append(link_text)

        text = "".join(content.itertext())
        # print(text)

        sentences = segment(text)
        print(colored(str(len(sentences)) + ' sentences', 'red'))
        print(colored(searchStr, 'red'))

        for sentence in sentences:
            # print(sentence)
            for search in searchStr:
                if (sentence == search): continue
                pos = sentence.find(search)
                if (pos > -1):
                    last = len(search) + pos
                    print(sentence[:pos], end='')
                    print(colored(search, 'green'), end='')
                    print(sentence[last:])
                    print('')

        print('')
        print('')
        print('')
