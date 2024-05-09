from logging import Logger, DEBUG
from cache.heartbeat import HarvestCacheHeartBeatThread


class HarvestConfiguration:
    api = {}
    cache = {}
    heartbeat: HarvestCacheHeartBeatThread = None
    indexes = {}
    logging = {}
    meta = {}
    plugins = {}
    reports = {}

    @staticmethod
    def load(filename: str = 'app/harvest.yaml'):
        from yaml import load, FullLoader

        with open(filename, 'r') as f:
            config = load(f, Loader=FullLoader)

        for key, value in config.items():
            setattr(HarvestConfiguration, key, value)

        from cache.connection import HarvestCacheConnection

        HarvestConfiguration.heartbeat = HarvestCacheHeartBeatThread(cache=HarvestCacheConnection(**HarvestConfiguration.cache),
                                                                     version=HarvestConfiguration.meta['version'])

        return HarvestConfiguration

    @staticmethod
    def load_reports() -> dict:
        import os
        import glob
        import site

        results = {}

        # Get the path of the site-packages directory
        site_packages_path = site.getsitepackages()[0]

        # Create a pattern for directories starting with 'CloudHarvest'
        pattern = os.path.join(site_packages_path, 'CloudHarvest*')

        # Iterate over all directories in the site-packages directory that match the pattern
        for directory in glob.glob(pattern):
            # Create a pattern for yaml files in a 'reports' subdirectory
            yaml_pattern = os.path.join(directory, '**/reports/**/*.yaml')

            # Iterate over all yaml files in 'reports' subdirectories
            for yaml_file in glob.glob(os.path.abspath(yaml_pattern)):
                yaml_file_abs = os.path.abspath(yaml_file)
                file_separated = yaml_file_abs.split(os.sep)
                root_report_dir_index = max([i for i in range(len(file_separated)) if file_separated[i] == 'reports'])
                report_name = '.'.join(file_separated[root_report_dir_index + 1:])[0:-5]

                with open(yaml_file_abs, 'r') as stream:
                    from yaml import load, FullLoader
                    report_contents = load(stream, Loader=FullLoader)

                results[report_name] = report_contents

        HarvestConfiguration.reports = results
        return results

        # from glob import glob
        # from logging import getLogger
        # from os.path import abspath, join, sep
        # logger = getLogger('harvest')
        #
        # results = {}
        # for search_path in search_paths:
        #     abs_path = abspath(join(search_path, '**/reports/**/*.yaml'))
        #     logger.debug(f'gathering report files from {abs_path}')
        #
        #     report_files = glob(abs_path, recursive=True)
        #
        #     logger.debug(f'found report files: {str(report_files)}')
        #     from yaml import load, FullLoader
        #     for file in report_files:
        #         logger.debug(f'load report: {file}')
        #
        #         with open(file, 'r') as stream:
        #             report_contents = load(stream, Loader=FullLoader)
        #
        #         file_separated = file.split(sep)
        #         root_report_dir_index = max([i for i in range(len(file_separated)) if file_separated[i] == 'reports'])
        #
        #         report_name = '.'.join(file_separated[root_report_dir_index + 1:])[0:-5]
        #
        #         if isinstance(report_contents, dict):
        #             results[report_name] = report_contents
        #
        #         else:
        #             logger.warning(f'could not load report {report_name} because it is not a valid dictionary object')
        #
        # return results

    @staticmethod
    def load_logger() -> Logger:
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
        with open('CloudHarvestApi/indexes.yaml', 'r') as f:
            from yaml import load, FullLoader
            indexes = load(f, Loader=FullLoader)

        HarvestConfiguration.indexes = indexes or {}

    @staticmethod
    def startup() -> None:
        from setup import config
        HarvestConfiguration.meta = config

        # loads configuration files
        HarvestConfiguration.load()

        # configures logging
        HarvestConfiguration.load_logger()

        # installs plugins
        from plugins import PluginRegistry
        PluginRegistry.plugins = HarvestConfiguration.plugins
        PluginRegistry.install()

        # locates reports
        HarvestConfiguration.load_reports()
