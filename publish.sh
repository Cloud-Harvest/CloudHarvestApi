#!/bin/bash

# publish.sh
# This script is used to build, test, and publish a Docker image for the Cloud Harvest API.
# It fetches the version number from meta.json and uses it along with the git commit's short name to tag the Docker image.
# The script also checks that all commits have been pushed to git and that the current branch is main.
# If the --dry-run or --skip-git-check flags are provided, the script will perform all steps except pushing the Docker image to the Docker registry and checking git status respectively.
# After pushing the Docker image to the Docker registry, the script tags the image as latest and pushes this tag to the Docker registry.
# The Docker namespace is configurable via the docker_namespace variable.
#
# Usage:
# ./publish.sh [--dry-run] [--skip-git-check]
#
# Options:
# --dry-run: Perform all steps except pushing the Docker image to the Docker registry.
# --skip-git-check: Skip the checks for the main branch and that all commits have been pushed.
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
skip_git_check=0

# Check for --dry-run and --skip-git-check flags
for arg in "$@"
do
    case $arg in
        --dry-run)
        dry_run=1
        shift # Remove --dry-run from processing
        ;;
        --skip-git-check)
        skip_git_check=1
        shift # Remove --skip-git-check from processing
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
    if ! which "$binary" > /dev/null 2>&1; then
        echo "$binary is not installed. Please install $binary and try again."
        exit 1
    fi
done

echo "All required binaries are installed."

# Fetch the version number from meta.json using bash and standard libraries/binaries only
version=$(grep -oP '(?<="version": ")[^"]*' meta.json)

echo "Version number fetched from meta.json: $version"

# Check that all commits have been pushed to git
if [ $skip_git_check -eq 0 ]; then
    if [ "$(git rev-parse --abbrev-ref HEAD)" != "main" ]; then
        echo "Not on main branch. Aborting."
        exit 1
    fi

    if [ "$(git rev-list origin/main..HEAD)" != "" ]; then
        echo "Not all commits have been pushed to git. Aborting."
        exit 1
    fi

  echo "Working on the main branch and all commits have been pushed to git."

fi

# Get the git commit's short-name
commit=$(git rev-parse --short HEAD)

echo "Git commit's short name: $commit"

name_version_commit="$image_name:$version-$commit"

# Build the docker container with --no-cache
docker build --no-cache -t "$name_version_commit" .

echo "Built docker container with tag: $name_version_commit"

# Tag the docker image
docker tag "$image_name:latest" "$name_version_commit"

# Start the container and run all of the tests in the tests directory
docker run -it --rm \
    --entrypoint="/bin/bash" \
    -v "./tests:/src/tests/" \
    "$name_version_commit" \
    -c "python -m unittest discover -s /src/tests/"

# Check the exit status of the tests
if [ $? -ne 0 ]; then
    echo "Tests failed. Aborting."
    exit 1
fi

echo "Tests passed."

# Check the value of dry_run
if [ $dry_run -eq 0 ]; then
    # Push the image to docker_namespace/image_name
    docker tag "$name_version_commit" "$docker_namespace/$name_version_commit"
    docker push "$docker_namespace/$name_version_commit"

    echo "Pushed $docker_namespace/$name_version_commit"

    # Tag the newly uploaded image as latest
    docker tag "$name_version_commit" "$docker_namespace/$image_name:latest"
    docker push "$docker_namespace/$image_name:latest"

    echo "Pushed $docker_namespace/$name_version_commit and tagged as latest"

else
    echo "Dry run completed successfully. No changes were pushed."
fi
