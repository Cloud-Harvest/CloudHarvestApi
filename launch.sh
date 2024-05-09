#!/bin/bash

# The  launch.sh script is a simple bash script that sets the UID and GID environment variables to the current user’s
#   UID and GID, respectively, and then runs  docker-compose up -d .

# The docker-compose.yml file is a Docker Compose file that defines the services that make up the application.

# Check if the app/harvest.yaml file exists
if [ ! -f "./app/harvest.yaml" ]; then
    # If the file does not exist, start config.py
    python3 config.py

    # Check the exit status of config.py
    if [ $? -ne 0 ]; then
        # If the exit status is not 0, abort the script
        echo "config.py exited with an error. Aborting."
        exit 1
    fi
fi
UID=$(id -u) GID=$(id -g) docker compose up # -d

