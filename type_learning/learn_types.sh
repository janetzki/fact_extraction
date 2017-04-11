#!/bin/bash

source ../venv/bin/activate
time nice -n 19 python type_learner.py
time nice -n 19 python type_cleaner.py
