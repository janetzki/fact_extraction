#!/bin/bash

source ../venv/bin/activate
time nice -n 10 python wikipedia_pattern_extractor.py | tee -a results_learning.log
time nice -n 10 python pattern_cleaner.py | tee -a results_cleaning.log
