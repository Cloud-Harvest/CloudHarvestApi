from logging import Logger, DEBUG



class HarvestConfiguration:
    api = {}
    cache = {}
    heartbeat = None
    indexes = {}
    logging = {}
    meta = {}
    plugins = {}
    reports = {}

    @staticmethod
    def load(filename: str = 'app/harvest.json'):
        from json import load

        with open(filename, 'r') as f:
            config = load(f)

        for key, value in config.items():
            setattr(HarvestConfiguration, key, value)

        from cache.connection import HarvestCacheConnection

        from cache.heartbeat import HarvestCacheHeartBeatThread
        HarvestConfiguration.heartbeat = HarvestCacheHeartBeatThread(cache=HarvestCacheConnection(**HarvestConfiguration.cache),
                                                                     version=HarvestConfiguration.meta['version'])

        return HarvestConfiguration

    @staticmethod
    def load_reports() -> dict:
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
                    with open(file, 'r') as stream:
                        report_contents = load(stream, Loader=FullLoader)

                    file_separated = file.split(os.sep)
                    root_report_dir_index = max([i for i in range(len(file_separated)) if file_separated[i] == 'reports'])
                    report_name = '.'.join(file_separated[root_report_dir_index + 1:])[0:-5]

                    results[report_name] = report_contents

        HarvestConfiguration.reports = results
        return results

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
        with open('meta.json', 'r') as meta_file_stream:
            from json import load
            meta = load(meta_file_stream)

        HarvestConfiguration.meta = meta

        # loads configuration files
        HarvestConfiguration.load()

        # configures logging
        HarvestConfiguration.load_logger()

        # locates reports
        HarvestConfiguration.load_reports()
