"""
cache.py - defines api-specific operations used for communicating with the backend cache
"""
from pymongo import MongoClient

from logging import getLogger
logger = getLogger('harvest')


class HarvestCacheConnection(MongoClient):
    def __init__(self, node: str, **kwargs):
        super().__init__(**kwargs)

        from uuid import uuid4
        self.id = str(uuid4())
        self.node = node
        self.session = None

        self._log_prefix = f'[{self.id}][{self.node}][{self.HOST}:{self.PORT}]'

    @property
    def is_connected(self) -> bool:
        """
        check if the connect is active
        :return: bool
        """

        try:
            self.list_databases()

        except Exception as ex:
            logger.debug(f'{self._log_prefix}: ' + ' '.join(ex.args))
            return False

        else:
            logger.debug(f'{self._log_prefix}: successful connection')
            return True

    def connect(self):
        # already connected; nothing else to do
        if self.is_connected:
            return self

        self.session = self.start_session()



        # you have to select a db/collection before querying
