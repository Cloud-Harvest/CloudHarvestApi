from logging import Logger, DEBUG
from plugins.registry import PluginRegistry
from cache.connection import HarvestCacheConnection
from cache.heartbeat import HarvestCacheHeartBeatThread


def load_configuration_files() -> dict:
    from os import environ
    import yaml

    custom_config = {}

    # load the default file
    with open('harvest/harvest.yaml') as default_file:
        default_config = yaml.load(default_file, Loader=yaml.FullLoader)

    # prioritize user's directive, home directory, then the expected /etc/harvest.d/api (when mounted by docker-compose)
    custom_config_path = _find_first_valid_path(environ.get('HARVEST_API_CONFIG'),
                                                '~/.harvest/api/harvest.yaml',
                                                '/etc/harvest.d/api/harvest.yaml')
    # load custom configurations
    if custom_config_path:
        with open(custom_config_path) as custom_file:
            custom_config = yaml.load(custom_file, Loader=yaml.FullLoader)

    # load version file
    with open('version') as version_file:
        version = version_file.read().strip()

        custom_config['version'] = version

    return default_config | custom_config


def load_logger(location: str, name: str = 'harvest', level: str = None, quiet: bool = False,
                **kwargs) -> Logger:
    """
    configures lagging for Harvest
    :param location: where log files should be stored
    :param name: internal log names
    :param level: sets the file and stream log levels
    :param quiet: hides stream output
    :return:
    """

    level = level if level is not None else 'info'

    from logging import getLogger, Formatter, StreamHandler
    from logging.handlers import RotatingFileHandler

    # startup
    logger = getLogger(name=name)

    from importlib import import_module
    lm = import_module('logging')
    log_level_attribute = getattr(lm, level.upper())

    # clear existing log handlers anytime this library is called
    [logger.removeHandler(handler) for handler in logger.handlers]

    # formatting
    log_format = Formatter(fmt='[%(asctime)s][%(levelname)s][%(filename)s] %(message)s')

    # file handler
    from pathlib import Path
    from os.path import expanduser
    _location = expanduser(location)

    # make the destination log directory if it does not already exist
    Path(_location).mkdir(parents=True, exist_ok=True)

    # configure the file handler
    from os.path import join
    fh = RotatingFileHandler(join(_location, 'harvest.api.log'), maxBytes=10000000, backupCount=5)
    fh.setFormatter(fmt=log_format)
    fh.setLevel(DEBUG)

    logger.addHandler(fh)

    if not quiet:
        # stream handler
        sh = StreamHandler()
        sh.setFormatter(fmt=log_format)
        sh.setLevel(log_level_attribute)
        logger.addHandler(sh)

    logger.setLevel(log_level_attribute)

    logger.debug('logging: enabled')

    return logger


def load_reports(*search_paths: str) -> dict:
    from glob import glob
    from logging import getLogger
    from os.path import abspath, join, sep
    logger = getLogger('harvest')

    results = {}
    for search_path in search_paths:
        abs_path = abspath(join(search_path, '**/reports/**/*.yaml'))
        logger.debug(f'gathering report files from {abs_path}')

        report_files = glob(abs_path, recursive=True)

        logger.debug(f'found report files: {str(report_files)}')
        from yaml import load, FullLoader
        for file in report_files:
            logger.debug(f'load report: {file}')

            with open(file, 'r') as stream:
                report_contents = load(stream, Loader=FullLoader)

            file_separated = file.split(sep)
            root_report_dir_index = max([i for i in range(len(file_separated)) if file_separated[i] == 'reports'])

            report_name = '.'.join(file_separated[root_report_dir_index + 1:])[0:-5]

            if isinstance(report_contents, dict):
                results[report_name] = report_contents

            else:
                logger.warning(f'could not load report {report_name} because it is not a valid dictionary object')

    return results


def _find_first_valid_path(*args) -> str or None:
    """
    returns the first path that exists given a list of paths
    performs os.path.expanduser() on each path
    """

    from os.path import abspath, expanduser, exists
    from os import PathLike

    for a in args:
        # expanduser() only expects str or PathLike
        if isinstance(a, (str, PathLike)):
            _a = abspath(expanduser(a))
            if exists(_a):
                return _a

    return None


api_configuration = load_configuration_files()


class HarvestConfiguration:
    api = api_configuration.get('api')
    cache_connection = HarvestCacheConnection(**api_configuration['cache']['connection'])
    heartbeat = HarvestCacheHeartBeatThread(cache=cache_connection, version=api_configuration['version'])
    logger = load_logger(**api_configuration.get('logging', {}))
    plugin_registry = PluginRegistry.initialize(**(api_configuration['modules'])).load()
    reports: dict = load_reports('./harvest', api_configuration.get('modules', {}).get('path'))

    @staticmethod
    def load(new_config: dict):
        for k, v in new_config.items():
            setattr(HarvestConfiguration, k, v)


if __name__ == '__main__':
    reports = load_reports()

    from pprint import pprint
    pprint(reports)
