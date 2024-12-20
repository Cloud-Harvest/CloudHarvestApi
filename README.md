# Cloud Harvest API
This repository provides an interface between clients, the server cache, and other apis. This program is intended to operation individually or as part of a cluster of API nodes. 

# Table of Contents
- [Configuration](#configuration)
  - [Location](#location)
  - [Config Tool Usage](#config-tool-usage)
  - [Default Silos](#default-silos)
  - [Custom Silos](#custom-silos)
  - [Read Only vs Read Write Silos](#read-only-vs-read-write-silos)
  - [Historical Context](#historical-context)
- [Building](#building)
- [Run](#run)
  - [launch.sh Usage](#launchsh-usage)
  - [Arguments](#arguments)
- [Silos](#silos)
- [License](#license)

# Configuration
A compiled configuration file is located at `./app/harvest.yaml` and has this basic structure:
```yaml
.default_mongo_database: &default_mongo_database
  database: harvest
  engine: mongo
  host: harvest-mongo
  password: default-harvest-password
  port: 27017
  username: harvest-api

api:
  connection:
    host: 127.0.0.1
    port: 8000
  logging:
    location: ./app/logs/
    level: DEBUG
    quiet: false

plugins:
    - branch: "main",
      url_or_package_name: "https://github.com/Cloud-Harvest/CloudHarvestPluginAws.git"

silos:
  harvest-core:
    <<: *default_mongo_database
    database: harvest
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


# Silos
Silos are data storage locations that Harvest uses for various operations. See the [SILOS.md](SILOS.md) file for more information.

# License
Shield: [![CC BY-NC-SA 4.0][cc-by-nc-sa-shield]][cc-by-nc-sa]

This work is licensed under a
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License][cc-by-nc-sa].

[![CC BY-NC-SA 4.0][cc-by-nc-sa-image]][cc-by-nc-sa]

[cc-by-nc-sa]: http://creativecommons.org/licenses/by-nc-sa/4.0/
[cc-by-nc-sa-image]: https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png
[cc-by-nc-sa-shield]: https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg
