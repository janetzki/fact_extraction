#!/bin/bash

BASEDIR=$(dirname "$0")

wget -vv nlp.stanford.edu/software/stanford-corenlp-full-2016-10-31.zip
unzip $BASEDIR/stanford-corenlp-full-2016-10-31.zip
rm $BASEDIR/stanford-corenlp-full-2016-10-31.zip
mv $BASEDIR/stanford-corenlp-full-2016-10-31 $BASEDIR/..