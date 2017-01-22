#!/bin/bash

wget -vv downloads.dbpedia.org/2016-04/core-i18n/en/redirects_en.ttl.bz2
bzip2 -dv redirects_en.ttl.bz2
mv redirects_en.ttl ../data/
python ../data_cleaning/redirects_extractor.py
python ../data_cleaning/redirects_substitutor.py