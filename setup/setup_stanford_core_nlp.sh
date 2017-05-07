#!/bin/bash

BASEDIR=$(dirname "$0")
UNCOMPRESSED="stanford-corenlp-full-2016-10-31"
DESTINATION="$BASEDIR/../$UNCOMPRESSED"
DOWNLOADFILE="$UNCOMPRESSED.zip"

if [ ! -d "$DESTINATION" ]; then
	if [ ! -d "$UNCOMPRESSED" ]; then
		if [ ! -e "$DOWNLOADFILE" ]; then
			wget -v nlp.stanford.edu/software/stanford-corenlp-full-2016-10-31.zip
		fi
		unzip $DOWNLOADFILE
		rm $DOWNLOADFILE
	fi
	mv $UNCOMPRESSED $DESTINATION
fi
