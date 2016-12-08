#!../venv/bin/python
# -*- coding: utf-8 -*-

import re
import sys
import os
from tqdm import tqdm
import csv
import codecs

delimiter = "#"
dump_path = '../data/enwiki-latest-pages-articles.xml'
dump_path_new = '../data/enwiki-latest-pages-articles-redirected.xml'
limit = 1e12
total_lines = 930000000
REGEX = re.compile('\[\[(.+?)(\|(.+?))?\]\]') # look for [[linked_article]] or [[linked_article|link_text]]

def unicode_csv_reader(utf8_data, dialect=csv.excel, **kwargs):
    csv_reader = csv.reader(utf8_data, dialect=dialect, **kwargs)
    for row in csv_reader:
        yield [unicode(cell, 'utf-8') for cell in row]

class Substitutor:
	def __init__(self, redirects_path='../data/redirects_en.txt'):
		self.redirects_path = redirects_path
		self.redirects = {}
		
		with open(redirects_path, 'r') as file:
			next(file)

			reader = unicode_csv_reader(file, delimiter=delimiter)
			for name, ressource in tqdm(reader, total=7340000):
				if name:
					self.redirects[name] = ressource

	def substitute(self, ressource, falseIfNone=False):
		if ressource in self.redirects:
			return self.redirects[ressource]
		
		if falseIfNone:
			return False
			
		return ressource
			
	def substitute_all(self, input):
		return REGEX.sub(self.substitute_match, input)
	
	# takes the match and substitutes the article link with the redirected article if available
	def substitute_match(self, match):
		ressource = self.substitute(match.group(1).replace(" ", "_"), True)
		if not ressource: # if no replacement done
			return match.group(0)
		# otherwise build new link string
		subst = "[["
		subst += ressource
		if match.group(3) != None: # if alternative text exists
			if not ressource == match.group(3): # check if article link is equal
				subst += match.group(2)
		else:
			subst += "|" + match.group(1) # add old link text as alternative text
		subst += "]]"
		return subst
		
	
if __name__ == '__main__':
	sub = Substitutor()
	line_counter = 0

	with open(dump_path, 'r', encoding="utf-8") as fin, open(dump_path_new, 'w', encoding="utf-8") as fout:
		for line in tqdm(fin, total=total_lines):
			fout.write(sub.substitute_all(line))
			
			line_counter +=1 
			if line_counter == limit:
				break
		fin.close()
		fout.close()
	