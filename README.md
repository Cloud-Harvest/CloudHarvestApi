# Cloud Harvest API
This repository provides an interface between clients, the server cache, and other apis. This program is intended to operation individually or as part of a cluster of API nodes. 

# Table of Contents
- [Configuration](#configpy)
  - [Location](#location) 
  - [Config Tool Usage](#config-tool-usage)
- [Building](#building)
- [Run](#run)
- [License](#license)


# config.py
First-time users are strongly encouraged to use the [config.py](config.py) script to generate a configuration file. This script will prompt for the necessary information and create a `harvest.json` file in `./app/harvest.json`.

## Location
A compiled configuration file is located at `./app/harvest.json` and has this basic structure:
```json
{
    "api": {
        "host": "0.0.0.0",
        "port": 8000
    },
    "cache": {
        "host": "cloudharvestapi-mongo-1",
        "password": "eoisjndfkvnzkdfjnbk",
        "port": 27017,
        "username": "harvest-api",
        "authsource": "harvest"
    },
    "logging": {
        "level": "debug",
        "location": "./app/logs/"
    },
    "plugins": {
        "https://github.com/Cloud-Harvest/CloudHarvestPluginAws.git": "main"
    }
}
```

## Config Tool Usage
```
Usage: config.py [-h] [--reset]

Cloud Harvest API Configuration Tool

Options:
  -h, --help  show this help message and exit
  --reset     Reset the configuration file to defaults
```

# Building
The API can be built locally using the following command:
```
docker compose build api
```

# Run
The API can be run by executing [`launch.sh`](launch.sh). The [configuration tool](#config-tool-usage) is automatically run if a configuration file is not found.

## launch.sh Usage
```bash
./launch.sh [--with-mongo]
```

## Arguments
| Argument       | Description                                                                                                                                                                                                                                                                                    |
|----------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `--with-mongo` | Starts a local MongoDB instance using the `mongo:latest` image. This is useful for testing and development purposes but also if you just want to run Harvest locally. For the purposes of using Harvest locally, leave the usernames and passwords as the defaults in the `harvest.json` file. |


# License
Shield: [![CC BY-NC-SA 4.0][cc-by-nc-sa-shield]][cc-by-nc-sa]

This work is licensed under a
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License][cc-by-nc-sa].

[![CC BY-NC-SA 4.0][cc-by-nc-sa-image]][cc-by-nc-sa]

[cc-by-nc-sa]: http://creativecommons.org/licenses/by-nc-sa/4.0/
[cc-by-nc-sa-image]: https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png
[cc-by-nc-sa-shield]: https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg
