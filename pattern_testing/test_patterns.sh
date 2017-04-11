#!/bin/bash

source ../venv/bin/activate
time nice -n 19 python pattern_tester.py | tee -a results.log
