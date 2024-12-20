# Cloud Harvest API
This repository provides an interface between clients, the server cache, and other apis. This program is intended to 
operate individually or as part of a cluster of API nodes. 

# Table of Contents
- [Configuration](#configuration)
- [Building](#building)
- [Run](#run)
  - [launch.sh Usage](#launchsh-usage)
  - [Arguments](#arguments)
- [Silos](#silos)
- [License](#license)

## Configuration
A compiled configuration file is located at `./app/harvest.yaml` and has this basic structure:

## Building
The API can be built locally using the following command:
```
docker compose build api
```

## Run
The API can be run by executing [the `launch` shell script](launch). 

Executing the script will also create the `app` directory. This directory will contain a copy of the `harvest.yaml` 
configuration file and the `logs` directory. You can accomplish these same steps with:

```bash
mkdir -p app/logs
cp -vn harvest.yaml app/harvest.yaml
```

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
