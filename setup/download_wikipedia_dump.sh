#!/bin/bash

BASEDIR=$(dirname "$0")

wget -vv dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles.xml.bz2
bzip2 -dv $BASEDIR/enwiki-latest-pages-articles.xml.bz2
mv $BASEDIR/enwiki-latest-pages-articles.xml $BASEDIR/../data/