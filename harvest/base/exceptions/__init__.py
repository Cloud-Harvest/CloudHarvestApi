from logging import getLogger
from typing import Literal

logger = getLogger('harvest')

_log_levels = Literal['debug', 'info', 'warning', 'error', 'critical']


class BaseHarvestException(BaseException):
    def __init__(self, *args, log_level: _log_levels = 'error'):
        super().__init__(*args)

        getattr(logger, log_level.upper())(' '.join(*args))


class BaseDataCollectionException(BaseHarvestException):
    def __init__(self, **kwargs):

        super(**kwargs).__init__()


class PluginImportException(BaseHarvestException):
    def __init__(self, *args):
        super().__init__(*args)


class BaseTaskException(BaseHarvestException):
    def __init__(self, *args):
        super().__init__(*args)
