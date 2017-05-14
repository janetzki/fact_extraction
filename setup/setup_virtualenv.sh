#!/bin/bash

BASEDIR=$(dirname "$0")

# Set up virtual environment using python 2.x
pip install virtualenv
virtualenv $BASEDIR/../venv -p python2

# start virtual environmet
source $BASEDIR/../venv/bin/activate

# Upgrade pip (may solve problems in the next step)
pip install -U pip

# Install requirements
pip install -r $BASEDIR/../requirements.txt

# Install SSLContext (optional, prevents warnings)
pip install requests[security]