#!/bin/bash

BASEDIR=$(dirname "$0")
UNCOMPRESSED="enwiki-latest-pages-articles.xml"
DESTINATION="$BASEDIR/../data/$UNCOMPRESSED"
DOWNLOADFILE="$UNCOMPRESSED.bz2"

if [ ! -d "$DESTINATION" ]; then
	if [ ! -d "$UNCOMPRESSED" ]; then
		if [ ! -e "$DOWNLOADFILE" ]; then
			wget -v dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles.xml.bz2
		fi
		bzip2 -dv $DOWNLOADFILE
	fi
	mv $UNCOMPRESSED $DESTINATION
fi
