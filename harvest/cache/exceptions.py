from base.exceptions import BaseHarvestException


class HarvestCacheException(BaseHarvestException):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
