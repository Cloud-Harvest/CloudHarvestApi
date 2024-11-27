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


# Silos
Silos are data storage locations that Harvest uses for various operations. Silos offer deployers the ability to
diversify their data storage locations and provide a more robust and resilient system. Alternatively, many Silos can be
colocated on the same server to provide a less complex system. Regardless of the deployment strategy, many Harvest systems
will leverage hard-coded Silos to provide consistent data storage.

Silos are defined in the Api configuration and are retrieved by [CloudHarvestAgents](https://github.com/Cloud-Harvest/CloudHarvestAgent)s
to perform tasks. Inconsistent Silo configurations can lead to task failures and data loss. Therefore, it is crucial to
ensure that all Api nodes have the same Silo configurations.

## Default Silos
| Name                   | Engine | Purpose                                                                                   |
|------------------------|--------|-------------------------------------------------------------------------------------------|
| `harvest-agents`       | Redis  | Where task executors are listed, monitored, and used.                                     |
| `harvest-core`         | Mongo  | Defines the location of the database used to administer the application and its metadata. |
| `harvest-plugin-aws`   | Mongo  | Where AWS data will live.                                                                 |
| `harvest-plugin-azure` | Mongo  | Where Azure data will live.                                                               |
| `harvest-tasks`        | Redis  | This shows active and queued tasks that executors process.                                |
| `harvest-task-results` | Redis  | Where task executor results are stored.                                                   |
| `harvest-tokens`       | Redis  | Ephemeral user tokens.                                                                    |
| `harvest-users`        | Mongo  | Defines the location of the Harvest user accounts and their associated privileges.        |

## Custom Silos
Deployers can also specify their own Silos in the `harvest.json` file. This is useful if you want to write TaskChains
which retrieve data from a specific location. For example, if you have a database that you want to use for a specific
report, you can define a Silo for that database and use it in your TaskChain like so:

```json
{
    "silos": {
      "my-silo-identifier": {
        "database": "db_name",
        "engine": "mysql",
        "host": "my-mysql-host",
        "password": "my-mysql-password",
        "port": 3306,
        "username": "my-mysql-username"
      }
    }
}
```

## Read Only vs Read Write Silos
Silos do not provide any native read-only or read-write functionality. Instead, deployers are responsible for ensuring
that their Silos are configured correctly. For example, if you want to use a read-only database for a specific report,
you must create a Silo which uses read only endpoints and user credentials. Similarly, if you want to use a read-write
database for a specific report, you must create a Silo which uses read-write endpoints and user credentials. The following
is an example of two custom Silo configurations which go to the same physical resource, but one is read-only and the other
is read-write:

```json
{
    "silos": {
      "my-silo-identifier": {
        "database": "db_name",
        "engine": "mysql",
        "host": "my-mysql-host",
        "password": "my-mysql-password",
        "port": 3306,
        "username": "my-mysql-username"
      },
      "my-silo-identifier-ro": {
        "database": "db_name",
        "engine": "mysql",
        "host": "my-mysql-host",
        "password": "my-mysql-read-only-password",
        "port": 3306,
        "username": "my-mysql-read-only-username"
      }
    }
}
```

As a general rule, we recommend using read-only Silos whenever possible to prevent accidental data loss. We also recommend
using load balancers to reduce read impact on the writer and to provide a more robust system.

## Historical Context
Silos were originally defined in [#44](https://github.com/Cloud-Harvest/CloudHarvestApi/issues/44). The following table
provides a list of Silos and their purposes.

# License
Shield: [![CC BY-NC-SA 4.0][cc-by-nc-sa-shield]][cc-by-nc-sa]

This work is licensed under a
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License][cc-by-nc-sa].

[![CC BY-NC-SA 4.0][cc-by-nc-sa-image]][cc-by-nc-sa]

[cc-by-nc-sa]: http://creativecommons.org/licenses/by-nc-sa/4.0/
[cc-by-nc-sa-image]: https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png
[cc-by-nc-sa-shield]: https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg
