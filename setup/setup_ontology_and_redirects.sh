#!/bin/bash

BASEDIR=$(dirname "$0")

wget -vv downloads.dbpedia.org/2016-04/core-i18n/en/instance_types_en.ttl.bz2
bzip2 -d $BASEDIR/instance_types_en.ttl.bz2
mv $BASEDIR/instance_types_en.ttl $BASEDIR/../data/

wget -vv downloads.dbpedia.org/2016-04/dbpedia_2016-04.nt
mv $BASEDIR/dbpedia_2016-04.nt $BASEDIR/../data/

wget -vv http://downloads.dbpedia.org/2016-04/links/yago_types.ttl.bz2
bzip2 -d $BASEDIR/yago_types.ttl.bz2
mv $BASEDIR/yago_types.ttl $BASEDIR/../data/

python $BASEDIR/../ttl_parsing/ttl_cleaner.py
python $BASEDIR/../setup/create_types_index.py
