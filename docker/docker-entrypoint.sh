#!/bin/bash

# Source the virtual environment
# Check if the plugins.txt file exists
# Install the plugins
# Run the application

source /venv/bin/activate \
&& touch -a /src/app/api/plugins.txt \
&& pip install -r /src/app/api/plugins.txt \
&& python /src/CloudHarvestApi/wsgi.py
