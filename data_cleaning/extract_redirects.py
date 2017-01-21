from tqdm import tqdm
import re
import os
import csv
import codecs

currentPath = os.path.dirname(os.path.abspath(__file__)) + '/'
redirects_path = '../data/redirects_en.ttl'
index_path = '../data/redirects_en.txt'
index_filtered_path = '../data/redirects.csv'
relations_path = currentPath + '../data/mappingbased_objects_en_extracted.csv'
delimiter = '#'  # '#' is never used as character in page titles
totalLines = 7339092  # TODO: replace magic number with line counter
limit = 1e12
REGEX = re.compile("<http://dbpedia.org/resource/(.*)> <.*> <http://dbpedia.org/resource/(.*)>.")


def dbpedia_url_to_resource(url):
    # "http://dbpedia.org/resource/Allan_Dwan" --> "Allan Dwan"
    resource = url[28:]
    return resource


def unicode_csv_reader(utf8_data, dialect=csv.excel, **kwargs):
    csv_reader = csv.reader(utf8_data, dialect=dialect, **kwargs)
    for row in csv_reader:
        yield [unicode(cell, 'utf-8') for cell in row]


def parse_ttl(input):
    match = REGEX.match(input)
    if match:
        return match.group(1), match.group(2)
    else:
        return False, False


def create_text_index():
    with open(redirects_path, 'r', encoding="utf8") as fin, open(index_path, 'w', encoding="utf8") as fout:
        line_counter = 0
        character_offset = 0

        for line in tqdm(fin, total=totalLines):
            name, resource = parse_ttl(line)

            if name:
                fout.write(name + delimiter + resource + '\n')

            character_offset += len(line)
            line_counter += 1
            if line_counter == limit:
                break


def filter_text_index():
    with open(index_path, 'r') as fin_index, \
            open(relations_path, 'r') as fin_relations, \
            codecs.open(index_filtered_path, 'w', encoding="utf8") as fout:

        relation_reader = csv.reader(fin_relations, delimiter=' ', quotechar='"')
        important_articles = set()

        tqdm.write("\n\nCollecting important articles...")
        for line in tqdm(relation_reader, total=500000):  # TODO: replace magic number with line counter
            # if "Cornelia" in dbpediaURLtoResource(line[2]):
            #	print("ja")

            important_articles.add(dbpedia_url_to_resource(line[2]))

        print(len(important_articles))
        # for a in important_articles:
        # print(a)
        print("Cornelia_de_Lange_syndrome".encode('utf-8') in important_articles)
        print(str("Stiles'_Tapaculo") in important_articles)
        index_reader = csv.reader(fin_index, delimiter=delimiter)
        tqdm.write("\n\nFiltering important articles...")
        for line in tqdm(index_reader, total=7400000):  # TODO: replace magic number with line counter
            # print(line[0])
            if line[0] in important_articles:
                fout.write(line[0] + delimiter + line[1] + '\n')
