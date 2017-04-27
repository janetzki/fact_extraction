#!/bin/bash

BASEDIR=$(dirname "$0")

wget -v nlp.stanford.edu/software/stanford-corenlp-full-2016-10-31.zip
unzip stanford-corenlp-full-2016-10-31.zip
rm stanford-corenlp-full-2016-10-31.zip
mv stanford-corenlp-full-2016-10-31 $BASEDIR/..