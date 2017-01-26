#!/bin/bash

./setup_virtualenv.sh
# start virtual environmet
source ../venv/bin/activate

./setup_stanford_core_nlp.sh
python setup_nltk.py

./download_dbpedia_relations.sh
./download_redirects.sh
./setup_ontology_and_redirects.sh

./download_wikipedia_dump.sh
./create_redirected_wikipedia_dump.sh
./create_wikipedia_dump_index.sh