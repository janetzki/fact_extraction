#!/bin/bash

BASEDIR=$(dirname "$0")

(cd $BASEDIR/.. && python -m wikipedia_connector.wikipedia_dump_index_creator)