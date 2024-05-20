#!/bin/bash

# The  launch.sh script is a simple bash script that sets the UID and GID environment variables to the current user’s
#   UID and GID, respectively, and then runs  docker-compose up -d .

# The docker-compose.yml file is a Docker Compose file that defines the services that make up the application.

# Initialize our own variables
with_mongo=0

# Check for --with-mongo flag
for arg in "$@"
do
    case $arg in
        --with-mongo)
        with_mongo=1
        shift # Remove --with-mongo from processing
        ;;
        *)
        shift # Remove generic argument from processing
        ;;
    esac
done

# Check if the app/harvest.json file exists
if [ ! -f "./app/harvest.json" ]; then
    # If the file does not exist, start config.py
    python3 config.py

    # Check the exit status of config.py
    if [ $? -ne 0 ]; then
        # If the exit status is not 0, abort the script
        echo "config.py exited with an error. Aborting."
        exit 1
    fi
fi

# Check the value of with_mongo
if [ $with_mongo -eq 1 ]; then
    echo "Starting the application with MongoDB"
    mkdir -p ./app/mongo/data ./app/mongo/logs
    UID=$(id -u) GID=$(id -g) docker compose up

else
    echo "Starting the API service"
    UID=$(id -u) GID=$(id -g) docker compose up api
fi
