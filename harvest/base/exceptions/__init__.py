from logging import getLogger
from typing import Iterable, Literal

logger = getLogger('harvest')

_log_levels = Literal['debug', 'info', 'warning', 'error', 'critical']


class BaseHarvestException(BaseException):
    def __init__(self, *args: Iterable[str], log_level: _log_levels = 'error'):
        super().__init__(*args)

        getattr(logger, log_level.lower())(' '.join(args))


class BaseDataCollectionException(BaseHarvestException):
    def __init__(self, **kwargs):

        super(**kwargs).__init__()


class BaseTaskException(BaseHarvestException):
    def __init__(self, *args):
        super().__init__(*args)
