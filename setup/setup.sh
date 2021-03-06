#!/bin/bash

BASEDIR=$(dirname "$0")

$BASEDIR/setup_virtualenv.sh
# start virtual environmet
source $BASEDIR/../venv/bin/activate

sudo apt-get install unzip
$BASEDIR/setup_stanford_core_nlp.sh
(cd $BASEDIR/.. && python -m setup.setup_nltk)

mkdir $BASEDIR/../data
$BASEDIR/download_dbpedia_relations.sh
$BASEDIR/download_redirects.sh
$BASEDIR/setup_ontology_and_redirects.sh

$BASEDIR/download_wikipedia_dump.sh
rmdir $BASEDIR/../downloads_temp/
$BASEDIR/create_redirected_wikipedia_dump.sh
$BASEDIR/create_wikipedia_dump_index.sh
