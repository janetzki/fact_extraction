#!/bin/bash

BASEDIR=$(dirname "$0")

wget -vv downloads.dbpedia.org/2016-04/core-i18n/en/mappingbased_objects_en.ttl.bz2
bzip2 -dv $BASEDIR/mappingbased_objects_en.ttl.bz2
mv $BASEDIR/mappingbased_objects_en.ttl $BASEDIR/../data/