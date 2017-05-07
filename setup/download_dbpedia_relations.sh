#!/bin/bash

BASEDIR=$(dirname "$0")
UNCOMPRESSED="mappingbased_objects_en.ttl"
DESTINATION="$BASEDIR/../data/$UNCOMPRESSED"
DOWNLOADFILE="$UNCOMPRESSED.bz2"

if [ ! -d "$DESTINATION" ]; then
	if [ ! -d "$UNCOMPRESSED" ]; then
		if [ ! -e "$DOWNLOADFILE" ]; then
			wget -v downloads.dbpedia.org/2016-04/core-i18n/en/mappingbased_objects_en.ttl.bz2
		fi
		bzip2 -dv $DOWNLOADFILE
	fi
	mv $UNCOMPRESSED $DESTINATION
fi
