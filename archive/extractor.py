import os
import imp

line_counting = imp.load_source('line_counting', '../helper_functions/line_counting.py')

mainPath = os.path.dirname(os.path.abspath(__file__)) + '/../data/'
pathObjects = mainPath + 'mappingbased_objects_en.ttl'
pathLiterals = mainPath + 'mappingbased_literals_en.ttl'
savePathObjects = mainPath + 'mappingbased_objects_en_filtered.csv'
savePathLiterals = mainPath + 'mappingbased_literals_en_filtered.csv'
maxLines = 0  # 0 means parse all lines


def filterTTL(relationships, path, saveInto):
    lines = line_counting.cached_counter.count_lines(path)
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


if __name__ == "__main__":
    relationships = ['almaMater', 'knownFor', 'occupation', 'award']
    print(filterTTL(relationships, pathObjects, savePathObjects))
