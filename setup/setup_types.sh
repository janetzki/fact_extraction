#!/bin/bash

wget -vv downloads.dbpedia.org/2015-10/core-i18n/en/instance_types_en.ttl.bz2
bzip2 -d instance_types_en.ttl.bz2
mv instance_types_en.ttl ../data/
python ../ontology_building/extract_types.py