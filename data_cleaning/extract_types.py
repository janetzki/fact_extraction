from tqdm import tqdm
import re
import sys, os, csv
import codecs

currentPath = os.path.dirname(os.path.abspath(__file__)) + '/'
redirects_path = '../data/instance_types_en.ttl'
output_path = '../data/types_en.csv'
delimiter = '#'  # '#' is never used as character in page titles
totalLines = 0
limit = 1e10
REGEX = re.compile("<http://dbpedia.org/resource/(.*)> <.*> <http://dbpedia.org/ontology/(.*)> \.")


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
            name, inst_type = parseTTL(line)

            if name and name.find("__") == -1:
                fout.write(name + delimiter + inst_type + '\n')

            lineCounter += 1
            if lineCounter == limit:
                break
        fin.close()
        fout.close()


if __name__ == '__main__':
    totalLines = rawpycount(redirects_path)

    extract()
