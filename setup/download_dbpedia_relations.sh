#!/bin/bash

BASEDIR=$(dirname "$0")

wget -v downloads.dbpedia.org/2016-04/core-i18n/en/mappingbased_objects_en.ttl.bz2
bzip2 -dv mappingbased_objects_en.ttl.bz2
mv mappingbased_objects_en.ttl $BASEDIR/../data/