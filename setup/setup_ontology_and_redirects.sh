#!/bin/bash

BASEDIR=$(dirname "$0")

wget -v downloads.dbpedia.org/2016-04/core-i18n/en/instance_types_en.ttl.bz2
bzip2 -d instance_types_en.ttl.bz2
mv instance_types_en.ttl $BASEDIR/../data/

wget -v downloads.dbpedia.org/2016-04/dbpedia_2016-04.nt
mv dbpedia_2016-04.nt $BASEDIR/../data/

wget -v http://downloads.dbpedia.org/2016-04/links/yago_types.ttl.bz2
bzip2 -d yago_types.ttl.bz2
mv yago_types.ttl $BASEDIR/../data/

python $BASEDIR/../ttl_parsing/ttl_cleaner.py
python $BASEDIR/../setup/create_types_index.py
