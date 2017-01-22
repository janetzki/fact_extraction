#!/bin/bash

./setup_virtualenv.sh
./setup_stanford_core_nlp.sh
python setup_nltk.py

./download_dbpedia_relations.sh
./setup_ontology.sh

./download_wikipedia_dump.sh
./create_redirected_wikipedia_dump.sh
./create_wikipedia_dump_index.sh