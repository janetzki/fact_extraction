#!/bin/bash

BASEDIR=$(dirname "$0")

# Set up virtual environment using python 2.x
virtualenv $BASEDIR/../venv -p python2

# Upgrade pip (may solve problems in the next step)
pip install -U pip

# Install requirements
pip install -r $BASEDIR/../requirements.txt

# Install SSLContext (optional, prevents warnings)
pip install requests[security]