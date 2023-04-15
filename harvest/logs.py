from logging import Logger


def setup(name: str = 'harvest', log_level: str = 'debug', quiet: bool = False) -> Logger:
    """
    configures lagging for Harvest; it
    :param name: log name
    :param log_level: sets the file and stream log levels
    :param quiet: hides stream output
    :return:
    """

    assert isinstance(log_level, str)
    assert isinstance(quiet, bool)

    from logging import getLogger, Formatter, StreamHandler
    from logging.handlers import RotatingFileHandler

    # startup
    logger = getLogger(name=name)

    from importlib import import_module
    lm = import_module('logging')
    log_level_attribute = getattr(lm, log_level.upper())

    # clear existing log handlers anytime this library is called
    [logger.removeHandler(handler) for handler in logger.handlers]

    # formatting
    log_format = Formatter()

    # file handler
    parent_path = '/var/log'
    from pathlib import Path
    Path(parent_path).mkdir(parents=True, exist_ok=True)

    from os.path import join
    fh = RotatingFileHandler(join(parent_path, 'harvest.api.log'), maxBytes=10000000, backupCount=5)
    fh.setFormatter(fmt=log_format)
    fh.setLevel(log_level_attribute)

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
