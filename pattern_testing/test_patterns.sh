#!/bin/bash

source ../venv/bin/activate
time nice -n 0 python pattern_tester.py | tee -a results.log
