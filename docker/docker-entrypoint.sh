#!/bin/bash

# Determine the base path
base_path="/src"
if [ ! -d "$base_path" ]; then
    base_path="."
fi

# Make the configuration directory for the app
subdirs=("certs" "logs")
for subdir in "${subdirs[@]}"; do
    mkdir -pv "$base_path/app/$subdir"
done

# Copy the configuration file to the app directory
# Use the -n flag to prevent overwriting the file
cp -nv "$base_path/harvest.yaml" "$base_path/app/harvest.yaml"

# Perform the following actions:
# 1. Activate the virtual environment
# 2. Generate the plugins.txt file
# 3. Install the plugins
# 4. Start the application
source "$base_path/venv/bin/activate" \
&& "$base_path/docker/make_plugins.txt.py" \
&& touch -a "$base_path/app/plugins.txt" \
&& pip install -r "$base_path/app/plugins.txt" \
&& python "$base_path/CloudHarvestApi"
