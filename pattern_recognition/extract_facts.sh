#!/bin/bash

source ../venv/bin/activate
time nice -n 10 python fact_extractor.py | tee -a results.log
