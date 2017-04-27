#!/bin/bash

BASEDIR=$(dirname "$0")

wget -vv downloads.dbpedia.org/2016-04/core-i18n/en/redirects_en.ttl.bz2
bzip2 -dv $BASEDIR/redirects_en.ttl.bz2
mv $BASEDIR/redirects_en.ttl $BASEDIR/../data/