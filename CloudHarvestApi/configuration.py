"""
Cloud Harvest API Configuration

This module provides the `HarvestConfiguration` class, which is responsible for loading and managing the configuration
for the Cloud Harvest API. It includes methods for loading configuration settings, setting up logging, and loading
reports.

Classes:
    HarvestConfiguration: A singleton class that stores and manages the configuration for the Cloud Harvest API.

Functions:
    HarvestConfiguration.load(filename: str = 'app/harvest.json'): Loads the configuration from the specified JSON file.
    HarvestConfiguration.load_reports() -> dict: Loads report files from the 'reports' directory.
    HarvestConfiguration.load_logger() -> Logger: Configures and returns the logger for the Cloud Harvest API.
    HarvestConfiguration.load_indexes(): Loads indexes from the 'indexes.yaml' file.
    HarvestConfiguration.startup() -> None: Initializes the configuration, logging, and reports for the Cloud Harvest API.

Usage:
    To load the configuration and initialize the API, call the `HarvestConfiguration.startup()` method.
"""

from logging import Logger, DEBUG


class HarvestConfiguration:
    """
    The HarvestConfiguration class is a singleton object that stores the configuration for the CloudHarvest API. This
    class is responsible for loading the configuration from the 'harvest.json' file, setting up the logging, and
    loading the reports from the 'reports' directory. The configuration is stored as class attributes and can be
    accessed using the dot notation.
    """

    api = {}
    heartbeat = None
    indexes = {}
    logging = {}
    meta = {}
    plugins = {}
    reports = {}
    silos = {}

    @staticmethod
    def _load(filename: str = 'app/harvest.json'):
        """
        This method loads the configuration from the 'harvest.json' file and stores it in the HarvestConfiguration class.
        """

        from json import load

        with open(filename) as f:
            config = load(f)

        for key, value in config.items():
            setattr(HarvestConfiguration, key, value)

        # Set up the backend silo connections

        # Ephemeral Silo (Redis) - API Heartbeat and Cache
        from CloudHarvestCoreTasks.silos.ephemeral import connect, start_heartbeat

        # Establish a connection to the Redis cache
        connect(**HarvestConfiguration.silos.get('ephemeral') | {'database': 'api'})

        # Start the heartbeat process using the 'api' heartbeat type
        HarvestConfiguration.heartbeat = start_heartbeat(heartbeat_type='api', database='api')

        # Persistent Silo (MongoDB) - API Retrieval
        from CloudHarvestCoreTasks.silos.persistent import connect
        connect(**HarvestConfiguration.silos.get('persistent'))

        return HarvestConfiguration

    @staticmethod
    def load_reports() -> dict:
        """
        This method locates all the report files in the 'reports' directory and loads them into the HarvestConfiguration
        class.
        """
        import os
        import glob
        import site

        results = {}
        site_packages_path = os.path.abspath(site.getsitepackages()[0])
        local_path = os.path.abspath('.')

        for path in [local_path, site_packages_path]:
            report_files = glob.glob(os.path.join(path, '**/*.yaml'), recursive=True)

            for file in report_files:
                if 'reports' in file and 'CloudHarvest' in file:
                    from yaml import load, FullLoader
                    with open(file) as stream:
                        report_contents = load(stream, Loader=FullLoader)

                    file_separated = file.split(os.sep)
                    root_report_dir_index = max([i for i in range(len(file_separated)) if file_separated[i] == 'reports'])
                    report_name = '.'.join(file_separated[root_report_dir_index + 1:])[0:-5]

                    results[report_name] = report_contents

        HarvestConfiguration.reports = results
        return results

    @staticmethod
    def _load_logger() -> Logger:
        """
        This method configures the logging for the CloudHarvest API using the configuration from the 'harvest.json' file.
        The logging level and location are set in the configuration file. The logger is returned for use in the API.
        """

        level = HarvestConfiguration.logging.get('level') or 'info'

        from logging import getLogger, Formatter, StreamHandler
        from logging.handlers import RotatingFileHandler

        # startup
        logger = getLogger(name='harvest')

        from importlib import import_module
        lm = import_module('logging')
        log_level_attribute = getattr(lm, level.upper())

        # clear existing log handlers anytime this library is called
        [logger.removeHandler(handler) for handler in logger.handlers]

        # formatting
        log_format = Formatter(fmt='[%(asctime)s][%(levelname)s][%(filename)s] %(message)s')

        # file handler
        from pathlib import Path
        from os.path import abspath
        _location = abspath(HarvestConfiguration.logging.get('location') or 'app/logs')

        # make the destination log directory if it does not already exist
        Path(_location).mkdir(parents=True, exist_ok=True)

        # configure the file handler
        from os.path import join
        fh = RotatingFileHandler(join(_location, 'api.log'), maxBytes=10000000, backupCount=5)
        fh.setFormatter(fmt=log_format)
        fh.setLevel(DEBUG)

        logger.addHandler(fh)

        if not HarvestConfiguration.reports.get('quiet'):
            # stream handler
            sh = StreamHandler()
            sh.setFormatter(fmt=log_format)
            sh.setLevel(log_level_attribute)
            logger.addHandler(sh)

        logger.setLevel(log_level_attribute)

        logger.debug('logging: enabled')

        return logger

    @staticmethod
    def load_indexes():
        """
        This method loads the indexes from the 'indexes.yaml' file and stores them in the HarvestConfiguration class.
        """

        with open('CloudHarvestApi/indexes.yaml') as f:
            from yaml import load, FullLoader
            indexes = load(f, Loader=FullLoader)

        HarvestConfiguration.indexes = indexes or {}

    @staticmethod
    def startup() -> None:
        """
        This method is called when the CloudHarvest API is started. It loads the configuration, sets up the logging, and
        loads the reports.
        """

        with open('meta.json') as meta_file_stream:
            from json import load
            meta = load(meta_file_stream)

        HarvestConfiguration.meta = meta

        # loads configuration files
        HarvestConfiguration._load()

        # configures logging
        HarvestConfiguration._load_logger()

        # locates reports
        HarvestConfiguration.load_reports()
