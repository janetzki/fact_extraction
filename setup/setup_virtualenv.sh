#!/bin/bash

# Set up virtual environment using python 2.x
virtualenv ../venv -p python2

# Activate virtual envirionment
source ../venv/bin/activate

# Upgrade pip (may solve problems in the next step)
pip install -U pip

# Install requirements
pip install -r ../requirements.txt

# Install SSLContext (optional, prevents warnings)
pip install requests[security]