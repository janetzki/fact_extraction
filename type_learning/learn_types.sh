#!/bin/bash

source ../venv/bin/activate
time nice -n 10 python type_learner.py
time nice -n 10 python type_cleaner.py
