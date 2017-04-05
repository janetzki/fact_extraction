#!/bin/bash

source ../venv/bin/activate
time nice -n 10 python wikipedia_pattern_extractor.py
time nice -n 10 python pattern_cleaner.py
