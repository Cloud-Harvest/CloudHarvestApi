"""
cache.py - defines api-specific operations used for communicating with the backend cache
"""
from pymongo import MongoClient

from logging import getLogger
logger = getLogger('harvest')


class HarvestCacheConnection(MongoClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.client = None

    @property
    def is_connected(self) -> bool:
        try:
            self.client

        except Exception as ex:
            logger.debug('cache: not connection to backend')
    def connect(self):
        self.client = self.start_session()
        self.client.client.