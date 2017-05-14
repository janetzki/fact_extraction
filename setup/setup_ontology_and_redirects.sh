#!/bin/bash

BASEDIR=$(dirname "$0")

$BASEDIR/download_file.sh downloads.dbpedia.org/2016-04/core-i18n/en/instance_types_en.ttl.bz2
$BASEDIR/download_file.sh downloads.dbpedia.org/2016-04/dbpedia_2016-04.nt
$BASEDIR/download_file.sh downloads.dbpedia.org/2016-04/links/yago_types.ttl.bz2

# start virtual environmet
source $BASEDIR/../venv/bin/activate

(cd $BASEDIR/.. && python -m nt_operations.nt_cleaner)
(cd $BASEDIR/.. && python -m setup.create_types_index)
