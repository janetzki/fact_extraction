#!/bin/bash

BASEDIR=$(dirname "$0")
UNCOMPRESSED="instance_types_en.ttl.xml"
DESTINATION="$BASEDIR/../data/$UNCOMPRESSED"
DOWNLOADFILE="$UNCOMPRESSED.bz2"

if [ ! -d "$DESTINATION" ]; then
	if [ ! -d "$UNCOMPRESSED" ]; then
		if [ ! -e "$DOWNLOADFILE" ]; then
			wget -v downloads.dbpedia.org/2016-04/core-i18n/en/instance_types_en.ttl.bz2
		fi
		bzip2 -dv $DOWNLOADFILE
	fi
	mv $UNCOMPRESSED $DESTINATION
fi



UNCOMPRESSED="dbpedia_2016-04.nt"
DESTINATION="$BASEDIR/../data/$UNCOMPRESSED"

wget -v downloads.dbpedia.org/2016-04/dbpedia_2016-04.nt
mv $UNCOMPRESSED $DESTINATION



UNCOMPRESSED="yago_types.ttl"
DESTINATION="$BASEDIR/../data/$UNCOMPRESSED"
DOWNLOADFILE="$UNCOMPRESSED.bz2"

if [ ! -d "$DESTINATION" ]; then
	if [ ! -d "$UNCOMPRESSED" ]; then
		if [ ! -e "$DOWNLOADFILE" ]; then
			wget -v http://downloads.dbpedia.org/2016-04/links/yago_types.ttl.bz2
		fi
		bzip2 -dv $DOWNLOADFILE
	fi
	mv $UNCOMPRESSED $DESTINATION
fi


# start virtual environmet
source $BASEDIR/../venv/bin/activate

python $BASEDIR/../nt_operations/nt_cleaner.py
python $BASEDIR/../setup/create_types_index.py
