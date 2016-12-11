import sys
import re
from collections import namedtuple
from itertools import takewhile
import os

currentPath = os.path.dirname(os.path.abspath(__file__)) + '\\'
pathObjects = currentPath + 'mappingbased_objects_en.ttl'
pathLiterals = currentPath + 'mappingbased_literals_en.ttl'
savePathObjects = currentPath + 'mappingbased_objects_en_extracted.csv'
savePathLiterals = currentPath + 'mappingbased_literals_en_extracted.csv'
maxLines = 0  # 0 means parse all lines


def main(argv):
    relationships = ['almaMater', 'knownFor', 'occupation', 'award']
    print(filterTTL(relationships, pathObjects, savePathObjects))


def filterTTL(relationships, path, saveInto):
    lines = rawpycount(path)
    relations = map(lambda s: '/' + s + '>', relationships)

    with open(path, 'r', encoding="utf8") as file:
        fout = open(saveInto, 'w', encoding="utf8")
        counter = [0] * len(relations)
        lineCounter = 0
        for line in file:
            # print(line)
            for i in range(len(relations)):
                rel = relations[i]
                if rel in line:
                    line = line.replace("<", "\"")
                    line = line.replace(">", "\"")
                    # print(line)
                    fout.write(line)
                    counter[i] += 1

            lineCounter += 1
            if (maxLines != 0 and lineCounter >= maxLines):
                break

            # print progress
            if lineCounter % 100000 == 0:
                print(str(int(100 * lineCounter / lines)) + "%")

        fout.close()
        return counter


def _make_gen(reader):
    b = reader(1024 * 1024)
    while b:
        yield b
        b = reader(1024 * 1024)


def rawpycount(filename):
    # http://stackoverflow.com/questions/19001402/how-to-count-the-total-number-of-lines-in-a-text-file-using-python
    f = open(filename, 'rb')
    f_gen = _make_gen(f.raw.read)
    return sum(buf.count(b'\n') for buf in f_gen)


if __name__ == "__main__":
    main(sys.argv)
