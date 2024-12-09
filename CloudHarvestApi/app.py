"""
This file contains the main static application class, CloudHarvestApi. This class contains the Flask application,
JobQueue instance, and configuration for the api. The run method is used to start.
"""

from logging import Logger


class CloudHarvestApi:
    """
    A static class which contains the Flask application, JobQueue instance, and configuration for the api.
    """
    from flask import Flask
    flask: Flask = None
    config = {}


    @staticmethod
    def run(**kwargs):
        """
        This method is used to start the api. It configures logging, creates the JobQueue, and starts the Flask
        application. It accepts all keyword arguments provided by the configuration file.
        """

        flat_kwargs = flatten_dict_preserve_lists(kwargs)

        # Configure logging
        logger = load_logging(log_destination=flat_kwargs.get('api.logging.location'),
                              log_level=flat_kwargs.get('api.logging.level'),
                              quiet=flat_kwargs.get('api.logging.quiet'))

        logger.info('Api configuration loaded successfully.')

        logger.info('Api starting')

        logger.info(f'Api startup complete. Will serve requests on {flat_kwargs.get("api.connection.host")}:{flat_kwargs["api.connection.port"]}.')

        logger.debug(CloudHarvestApi.flask.url_map)

        # Start the Flask application
        CloudHarvestApi.flask.run(host=flat_kwargs.get('api.connection.host', 'localhost'),
                                    port=flat_kwargs.get('api.connection.port', 8000))


def flatten_dict_preserve_lists(d, parent_key='', sep='.') -> dict:
    """
    Flattens a dictionary while preserving lists.

    Arguments
    d (dict): The dictionary to flatten.
    parent_key (str, optional): The parent key. Defaults to ''.
    sep (str, optional): The separator to use. Defaults to '.'.

    Returns
    dict: The flattened dictionary.
    """
    items = []

    for k, v in d.items():
        new_key = f'{parent_key}{sep}{k}' if parent_key else k

        if isinstance(v, dict):
            items.extend(flatten_dict_preserve_lists(v, new_key, sep=sep).items())

        else:
            items.append((new_key, v))

    return dict(items)


#############################################
# Startup methods                           #
#############################################

def load_configuration_from_file() -> dict:
    from yaml import load, FullLoader

    configuration = {}

    # Select the first file of the list
    for filename in ('./app/harvest.yaml', './harvest.yaml'):
        from os.path import exists

        if exists(filename):
            with open(filename) as agent_file:
                configuration = load(agent_file, Loader=FullLoader)

            break

    # Remove any keys that start with a period. This allows YAML anchors to be used in the configuration file.
    return {
        k:v
        for k, v in configuration.items() or {}
        if not k.startswith('.')
    }

def load_logging(log_destination: str = './app/logs/', log_level: str = 'info', quiet: bool = False, **kwargs) -> Logger:
    """
    This method configures logging for the api.

    Arguments
    log_destination (str, optional): The destination directory for the log file. Defaults to './app/logs/'.
    log_level (str, optional): The logging level. Defaults to 'info'.
    quiet (bool, optional): Whether to suppress console output. Defaults to False.
    """
    level = log_level

    from logging import getLogger, Formatter, StreamHandler, DEBUG
    from logging.handlers import RotatingFileHandler

    # startup
    new_logger = getLogger(name='harvest')

    # If the logger exists, remove all of its existing handlers
    if new_logger.hasHandlers():
        [
            new_logger.removeHandler(handler)
            for handler in new_logger.handlers
        ]

    from importlib import import_module
    lm = import_module('logging')
    log_level_attribute = getattr(lm, level.upper())

    # formatting
    log_format = Formatter(fmt='[%(asctime)s][%(levelname)s][%(filename)s] %(message)s')

    # file handler
    from pathlib import Path
    from os.path import abspath, expanduser
    _location = abspath(expanduser(log_destination))

    # make the destination log directory if it does not already exist
    Path(_location).mkdir(parents=True, exist_ok=True)

    # configure the file handler
    from os.path import join
    fh = RotatingFileHandler(join(_location, 'api.log'), maxBytes=10000000, backupCount=5)
    fh.setFormatter(fmt=log_format)
    fh.setLevel(DEBUG)

    new_logger.addHandler(fh)

    if not quiet:
        # stream handler
        sh = StreamHandler()
        sh.setFormatter(fmt=log_format)
        sh.setLevel(log_level_attribute)
        new_logger.addHandler(sh)

    new_logger.setLevel(log_level_attribute)

    new_logger.debug(f'Logging enabled successfully. Log location: {log_destination}')

    return new_logger

def load_silos(silo_config: dict) -> dict:
    """
    This method loads the silos from the configuration.

    Arguments
    silo_config (dict): The silo configuration.

    Returns
    dict: The silo objects.
    """
    from logging import getLogger
    from CloudHarvestCoreTasks.silos import add_silo

    logger = getLogger('harvest')

    results = {}

    # Create the silo objects
    for silo_name, silo_configuration in silo_config.items():
        new_silo_indexes = silo_configuration.pop('indexes', None)

        new_silo = add_silo(name=silo_name, **silo_configuration)

        if new_silo.is_connected:
            logger.info(f'{silo_name}: Connected successfully.')

            if new_silo_indexes:
                logger.info(f'{silo_name}: Adding indexes.')
                new_silo.add_indexes(new_silo_indexes)

            results[silo_name] = 'success'

        else:
            logger.error(f'Silo {silo_name} failed to connect.')
            results[silo_name] = 'failure'

    return results
