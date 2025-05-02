from CloudHarvestCoreTasks.dataset import WalkableDict

from logging import Logger

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


def start_node_heartbeat(config: WalkableDict):
    """
    Start the heartbeat process on the harvest-nodes silo. This process will update the node status in the Redis
    cache at regular intervals.

    Args:
    config (WalkableDict): The configuration for the node heartbeat process.

    Example:
        >>> # Start the heartbeat process with a 5x expiration multiplier and a check rate of 1 second. The API will be
        >>> # considered offline if it has not updated its status in 5 seconds.
        >>> start_node_heartbeat(expiration_multiplier=5, heartbeat_check_rate=1)
        >>>
        >>> # Start the heartbeat process with an expiration multiplier of 10 and a check rate of 2 seconds. The API will
        >>> # be considered offline if it has not updated its status in 10 seconds.
        >>> start_node_heartbeat(expiration_multiplier=10, heartbeat_check_rate=2)

    Returns: The thread object that is running the heartbeat process.
    """

    heartbeat_check_rate = config.walk('api.heartbeat.check_rate') or 1
    expiration_multiplier = config.walk('api.heartbeat.expiration_multiplier') or 5

    import platform

    from CloudHarvestCoreTasks.silos import get_silo
    from datetime import datetime, timezone
    from logging import getLogger
    from socket import getfqdn, gethostbyname
    from time import sleep
    from threading import Thread

    logger = getLogger('harvest')

    def _thread():
        start_datetime = datetime.now(tz=timezone.utc)

        # Get the Redis client
        silo = get_silo('harvest-nodes')
        client = silo.connect()     # A StrictRedis instance

        # Get the application metadata
        import json
        with open('./meta.json') as meta_file:
            app_metadata = json.load(meta_file)

            node_name = platform.node()
            node_role = 'api'

            node_info = {
                "architecture": f'{platform.machine()}',
                "ip": gethostbyname(getfqdn()),
                "heartbeat_seconds": heartbeat_check_rate,
                "name": node_name,
                "os": platform.freedesktop_os_release().get('PRETTY_NAME'),
                "pid": config.walk('api.pid'),
                "plugins": config.get('plugins', []),
                "port": config.walk('api.connection.port'),
                "python": platform.python_version(),
                "role": node_role,
                "start": start_datetime.isoformat(),
                "version": app_metadata.get('version')
            }

        while True:
            # Update the last heartbeat time
            last_datetime = datetime.now(tz=timezone.utc)
            node_info['last'] = last_datetime.isoformat()
            node_info['duration'] = (last_datetime - start_datetime).total_seconds()

            # Update the node status in the Redis cache
            try:
                node_record_identifier = f'{node_role}::{node_name}::{node_info["port"]}'

                client.setex(name=node_record_identifier,
                             value=json.dumps(node_info, default=str),
                             time=int(expiration_multiplier * heartbeat_check_rate))

                logger.debug(f'heartbeat: OK')

            except Exception as e:
                logger.error(f'heartbeat: Could not update silo `harvest-nodes`: {e.args}')

            sleep(heartbeat_check_rate)

    # Start the heartbeat thread
    thread = Thread(target=_thread, daemon=True)
    thread.start()

    return thread

#############################################
# Startup methods                           #
#############################################

def load_configuration_from_file() -> dict:
    from yaml import load, FullLoader

    configuration = {}

    from os.path import abspath, expanduser, exists
    config_paths = (
        abspath(expanduser('./app/harvest.yaml')),
        abspath(expanduser('./harvest.yaml')),
    )

    # Select the first file of the list
    for filename in config_paths:

        if exists(filename):
            with open(filename) as agent_file:
                configuration = load(agent_file, Loader=FullLoader)

            break

    if not configuration:
        raise FileNotFoundError(f'No configuration file found in {config_paths}.')

    # Remove any keys that start with a period. This allows YAML anchors to be used in the configuration file.
    return {
        k:v
        for k, v in configuration.items() or {}.items()
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
    log_format = Formatter(fmt='[%(asctime)s][%(process)d][%(levelname)s][%(filename)s] %(message)s')

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
        try:
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

        except Exception as ex:
            logger.error(f'Could not load silo {silo_name}: {ex.args[0]}')
            results[silo_name] = 'failure'

    return results
