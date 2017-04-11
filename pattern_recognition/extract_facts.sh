#!/bin/bash

source ../venv/bin/activate
time nice -n 19 python fact_extractor.py | tee -a results.log
