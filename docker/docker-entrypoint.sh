#!/bin/bash

    # Determine the base path
    base_path=$(realpath "/src")
    if [ ! -d "$base_path" ]; then
        base_path=$(realpath ".")
    fi

    # Script parameters
    app_name="CloudHarvestApi"

    # Default values for options
    host="0.0.0.0"
    port="8000"
    pemfile="$base_path/app/harvest-self-signed.pem"
    debug=0
    workers=1

    # Parse command-line arguments
    while [[ "$#" -gt 0 ]]; do
        case $1 in
            --host) host="$2"; shift ;;
            --port) port="$2"; shift ;;
            --pemfile) pemfile="$2"; shift ;;
            --debug) debug=1 ;;
            --workers) workers="$2"; shift ;;
            --help)
                # Echo the launcher script's help message
                echo "$app_name Usage: [options]"
                echo
                echo "Options:"
                echo "  --host <host>        Host to bind to (default: $host)"
                echo "  --port <port>        Port to bind to (default: $port)"
                echo "  --pemfile <file>     Path to the PEM file (default: $pemfile)"
                echo "  --debug              Enable debug mode"
                echo "  --workers <num>      Number of gunicorn workers (default: $workers)"
                echo "  --help               Show this help message"

                exit 0
                ;;
            *) echo "Unknown parameter: $1"; exit 1 ;;
        esac
        shift
    done

    # Make the configuration directory for the app
    subdirs=("logs")
    for subdir in "${subdirs[@]}"; do
        mkdir -pv "$base_path/app/$subdir"
    done

    # Copy the configuration file to the app directory
    # Use the -n flag to prevent overwriting the file
    cp -nv "$base_path/harvest.yaml" "$base_path/app/harvest.yaml"

    # Start the application
    if [[ "$debug" -eq 1 ]]; then
        # Debug mode: Pass all parameters to the Python script
        source "$base_path/venv/bin/activate" \
        && export PYTHONPATH="$base_path" \
        && python "$base_path/$app_name" --host "$host" --port "$port" --pemfile "$pemfile" --debug
    else
        # Production mode: Use Gunicorn
        source "$base_path/venv/bin/activate" \
        && export PYTHONPATH="$base_path" \
        && gunicorn -w "$workers" -b "$host:$port" --certfile "$pemfile" --keyfile "$pemfile" "$base_path/$app_name/__main__:app"
    fi

