from logging import getLogger
from pymongo import MongoClient

logger = getLogger('harvest')


class HarvestCacheConnection(MongoClient):
    def __init__(self, node: str, **kwargs):
        """
        creates a connection to the Mongo backend
        :param node: an ambiguous name for a database endpoint
        :param kwargs: pymongo connection arguments (host, port, username, password, tlsCAFile)
        """
        super().__init__(**kwargs)

        from uuid import uuid4
        self.id = str(uuid4())
        self.node = node
        self.session = None

        self.log_prefix = f'[{self.id}][{self.node}][{self.HOST}:{self.PORT}]'

    def connect(self):
        """
        creates a new session if one is needed
        :return:
        """
        # already connected; nothing else to do
        if self.is_connected:
            return self

        self.session = self.start_session()
        return self

    def is_connected(self) -> bool:
        """
        check if the connect is active
        :return: bool
        """

        try:
            self.server_info()

        except Exception as ex:
            logger.debug(f'{self.log_prefix}: ' + ' '.join(ex.args))
            return False

        else:
            logger.debug(f'{self.log_prefix}: successful connection')
            return True

