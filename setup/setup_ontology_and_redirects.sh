#!/bin/bash

wget -vv downloads.dbpedia.org/2016-04/core-i18n/en/instance_types_en.ttl.bz2
bzip2 -d instance_types_en.ttl.bz2
mv instance_types_en.ttl ../data/

wget -vv downloads.dbpedia.org/2016-04/dbpedia_2016-04.nt
mv dbpedia_2016-04.nt ../data/

wget -vv http://downloads.dbpedia.org/2016-04/links/yago_types.ttl.bz2
bzip2 -d yago_types.ttl.bz2
mv yago_types.ttl ../data/

python ../ttl_parsing/ttl_cleaner.py
python ../setup/create_types_index.py
