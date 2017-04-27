#!/bin/bash

BASEDIR=$(dirname "$0")

wget -v dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles.xml.bz2
bzip2 -dv enwiki-latest-pages-articles.xml.bz2
mv enwiki-latest-pages-articles.xml $BASEDIR/../data/