from logging import getLogger
from typing import Literal

logger = getLogger('harvest')

_log_levels = Literal['debug', 'info', 'warning', 'error', 'critical']


class PluginImportException(BaseException):
    def __init__(self, *args, log_level: str = _log_levels):
        super().__init__(*args)

        getattr(logger, log_level.upper())(' '.join(*args))
