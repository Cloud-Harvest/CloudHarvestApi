import pytest
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL


@pytest.mark.parametrize("log_level,quiet,expected_level,expected_handlers",
                         [('debug', False, DEBUG, 2),
                          ('info', False, INFO, 2),
                          ('warning', False, WARNING, 2),
                          ('error', False, ERROR, 2),
                          ('critical', False, CRITICAL, 2),
                          ('debug', True, DEBUG, 1)])
def test_get_logger(log_level: str, quiet: bool, expected_level: int, expected_handlers: int):
    import startup
    from logging import Logger

    test_log_name = f'harvest-{log_level}-{str(quiet)}'

    logger = startup.get_logger(name=test_log_name, log_level=log_level, quiet=quiet)

    # assert we got a Logger class back
    assert isinstance(logger, Logger)

    # assert logger name
    assert logger.name == test_log_name

    # assert log level
    for handler in logger.handlers:
        assert handler.level == expected_level

    # assert number of handlers
    assert len(logger.handlers) == expected_handlers


def test_load_configuration_files():
    import startup

    result = startup.load_configuration_files()

    assert isinstance(result, dict)

    for key in ('cache', 'logging'):
        assert key in result.keys()