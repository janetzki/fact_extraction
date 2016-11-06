import sys
import re
from collections import namedtuple
from itertools import takewhile

pathObjects = 'C:/Users/Nirwana/Private Dokumente/ITSE/16.17/KDLD/Turtle Parse/mappingbased_objects_en.ttl'
pathLiterals = 'C:/Users/Nirwana/Private Dokumente/ITSE/16.17/KDLD/Turtle Parse/mappingbased_literals_en.ttl'
savePathObjects = 'C:/Users/Nirwana/Private Dokumente/ITSE/16.17/KDLD/Turtle Parse/mappingbased_objects_en_extracted.csv'
savePathLiterals = 'C:/Users/Nirwana/Private Dokumente/ITSE/16.17/KDLD/Turtle Parse/mappingbased_literals_en_extracted.csv'
maxLines = 100 # 0 means parse all lines

def main(argv):
	#print(filterTTL(pathObjects, savePathObjects))
	print(filterTTL(pathLiterals, savePathLiterals))

def filterTTL(path, saveInto):
	#lines = num_lines = sum(1 for line in open(path))
	#print lines
	with open(path, 'r') as file:
		fout = open(saveInto,'w')
		relations = ['/almaMater>', '/knownFor>', '/occupation>', '/award>']
		lineCounter = 0
		hits = 0
		for line in file:
			print line
			for rel in relations:
				if(rel in line):
					line = line.replace("<", "\"")
					line = line.replace(">", "\"")
					#print(line)
					fout.write(line)
					hits += 1

			lineCounter += 1
			#print(100 * lineCounter / lines)
			if(maxLines != 0 and lineCounter >= maxLines):
				break
				
		fout.close()
		return hits
	
if __name__ == "__main__":
	main(sys.argv)