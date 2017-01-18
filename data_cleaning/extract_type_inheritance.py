from tqdm import tqdm
import re
import os
import imp

line_counting = imp.load_source('line_counting', '../helper_functions/line_counting.py')

currentPath = os.path.dirname(os.path.abspath(__file__)) + '/'
redirects_path = '../data/dbpedia_2016-04.nt'
output_path = '../data/types_inheritance_en.csv'
delimiter = '#'  # '#' is never used as character in page titles
totalLines = 0
limit = 1e10
REGEX = re.compile(
    "<http://dbpedia.org/ontology/(.*)> " +
    "<http://www.w3.org/2000/01/rdf-schema#subClassOf> " +
    "<http://dbpedia.org/ontology/(.*)> \.")


def parseTTL(input):
    match = REGEX.match(input)
    if match:
        return match.group(1), match.group(2)
    else:
        return False, False


def extract():
    with open(redirects_path, 'r') as fin, open(output_path, 'w') as fout:
        lineCounter = 0

        fout.write('"sep=' + delimiter + '"\n')

        tqdm.write('\n\nType extraction...')
        for line in tqdm(fin, total=totalLines):
            subclass, parentclass = parseTTL(line)

            if subclass and subclass.find("__") == -1:
                fout.write(subclass + delimiter + parentclass + '\n')

            lineCounter += 1
            if lineCounter == limit:
                break
        fin.close()
        fout.close()


if __name__ == '__main__':
    totalLines = line_counting.count_lines(redirects_path)
    extract()
