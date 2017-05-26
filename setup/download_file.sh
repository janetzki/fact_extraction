#!/bin/bash

BASEDIR=$(dirname "$0")
TEMP="$BASEDIR/../downloads_temp"

USAGE="Usage: download_file.sh <url> (destination)"
if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    	echo $USAGE
    	exit 1
fi

URL=$1
DOWNLOADFILE="$TEMP/${URL##*/}"
EXTENSION="${DOWNLOADFILE##*.}"
DECOMPRESSED="${DOWNLOADFILE%.*}"

if [ "$EXTENSION" != "zip" ] && [ "$EXTENSION" != "bz2" ]; then
	echo "Invalid compressed file extension: $EXTENSION, skipping decompression"
	echo "Valid extensions are: .zip .bz2"
	DECOMPRESSED="$DOWNLOADFILE"
fi

BASENAME="${DECOMPRESSED##*/}"

if [[ $BASENAME != *"."* ]]; then
	DECOMPRESSED="$DECOMPRESSED/" # It is a directory.
	BASENAME="$BASENAME/"
fi

if [ "$#" -lt 2 ]; then
	DESTINATION="$BASEDIR/../data/$BASENAME"
else
	DESTINATION=$2
fi

echo "-----------------------"
echo "Download file from url: $URL"
echo "File: $DOWNLOADFILE"
echo "File extension: $EXTENSION"
echo "Decompressed file or directory: $DECOMPRESSED"
echo "Destination file or directory: $DESTINATION"
echo "-----------------------"

if [ ! -e "$DESTINATION" ] && [ ! -d "$DESTINATION" ]; then
	if [ ! -e "$DECOMPRESSED" ] && [ ! -d "$DECOMPRESSED" ]; then
		if [ ! -e "$DOWNLOADFILE" ]; then
			wget -v $URL -P $TEMP
		else
			echo "$DOWNLOADFILE already exists, skipping download"
		fi

		if [ "$EXTENSION" == "zip" ]; then
			(unzip $DOWNLOADFILE -d $DECOMPRESSED && rm $DOWNLOADFILE)
		elif [ "$EXTENSION" == "bz2" ]; then
			bzip2 -dv $DOWNLOADFILE
		fi
	else
		echo "$DECOMPRESSED already exists, skipping download and decompression"
	fi
	mv $DECOMPRESSED $DESTINATION
else
	echo "$DESTINATION already exists, skipping download and decompression"
fi
