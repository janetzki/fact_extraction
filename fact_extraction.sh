#!/bin/bash

BASEDIR=$(dirname "$0")

$BASEDIR/type_learning/learn_types.sh
$BASEDIR/pattern_learning/learn_patterns.sh
$BASEDIR/pattern_recognition/extract_facts.sh
