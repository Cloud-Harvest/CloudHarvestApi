#!/bin/bash

# publish.sh
# This script is used to build, test, and publish a Docker image for the Cloud Harvest API.
# It fetches the version number from meta.json and uses it along with the git commit's short name to tag the Docker image.
# The script also checks that all commits have been pushed to git and that the current branch is master.
# If the --dry-run flag is provided, the script will perform all steps except pushing the Docker image to the Docker registry.
# After pushing the Docker image to the Docker registry, the script tags the image as latest and pushes this tag to the Docker registry.
# The Docker namespace is configurable via the docker_namespace variable.
#
# Usage:
# ./publish.sh [--dry-run]
#
# Options:
# --dry-run: Perform all steps except pushing the Docker image to the Docker registry.
#
# Environment Variables:
# image_name: The name of the Docker image. Default is "cloud-harvest-api".
# docker_namespace: The Docker namespace where the Docker image will be pushed. Default is "fionajuneleathers".
#
# Note: This script requires Docker, git, and grep to be installed and properly configured on the system where it will be run.

# Initialize our own variables
dry_run=0
image_name="cloud-harvest-api"
docker_namespace="fionajuneleathers"

# Check for --dry-run flag
for arg in "$@"
do
    case $arg in
        --dry-run)
        dry_run=1
        shift # Remove --dry-run from processing
        ;;
        *)
        shift # Remove generic argument from processing
        ;;
    esac
done

# List of required binaries
required_binaries=("docker" "git" "grep")

# Loop through each binary and check if it's installed
for binary in "${required_binaries[@]}"; do
    if ! where "$binary" > /dev/null 2>&1; then
        echo "$binary is not installed. Please install $binary and try again."
        exit 1
    fi
done

# Fetch the version number from meta.json using bash and standard libraries/binaries only
version=$(grep -oP '(?<="version": ")[^"]*' meta.json)

# Check that all commits have been pushed to git
if [ "$(git rev-parse --abbrev-ref HEAD)" != "master" ]; then
    echo "Not on master branch. Aborting."
    exit 1
fi

if [ "$(git rev-list origin/master..HEAD)" != "" ]; then
    echo "Not all commits have been pushed to git. Aborting."
    exit 1
fi

# Build the docker container with --no-cache
docker build --no-cache -t $image_name .

# Get the git commit's short-name
commit=$(git rev-parse --short HEAD)

name_version_commit="$image_name:$version-$commit"

# Tag the docker image
docker tag "$image_name:latest" "$name_version_commit"

# Start the container and run all of the tests in the tests directory
docker run -v $(pwd)/tests:/tests "$name_version_commit" /bin/bash -c "python -m unittest discover -s /tests"

# Check the exit status of the tests
if [ $? -ne 0 ]; then
    echo "Tests failed. Aborting."
    exit 1
fi

# Check the value of dry_run
if [ $dry_run -eq 0 ]; then
    # Push the image to docker_namespace/image_name
    docker tag "$name_version_commit" "$docker_namespace/$name_version_commit"
    docker push "$docker_namespace/$name_version_commit"

    # Tag the newly uploaded image as latest
    docker tag "$name_version_commit" "$docker_namespace/$image_name:latest"
    docker push "$docker_namespace/$image_name:latest"

    echo "Pushed $docker_namespace/$name_version_commit and tagged as latest"
else
    echo "Dry run completed successfully. No changes were pushed."
fi
