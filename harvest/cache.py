"""
cache.py - defines api-specific operations used for communicating with the backend cache
"""
from bson import ObjectId
from pymongo import MongoClient
from logging import getLogger
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

        self._log_prefix = f'[{self.id}][{self.node}][{self.HOST}:{self.PORT}]'

    @property
    def is_connected(self) -> bool:
        """
        check if the connect is active
        :return: bool
        """

        try:
            self.server_info()

        except Exception as ex:
            logger.debug(f'{self._log_prefix}: ' + ' '.join(ex.args))
            return False

        else:
            logger.debug(f'{self._log_prefix}: successful connection')
            return True

    def add_indexes(self, indexes: dict):
        """
        create an index in the backend cache
        :param indexes: a dictionary of the {database: {collection: [fielda, fieldb]}} construct
        :return:
        """
        # verify connection
        self.connect()

        # identify databases
        for database in indexes.keys():
            # identify collections
            for collection in indexes[database].keys():
                # identify indexes
                for index in indexes[database][collection]:
                    self[database][collection].create_index(keys=index)
                    logger.debug(f'{self._log_prefix}: added index: {database}.{collection}.{str(index)}')

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

    def set_pstar(self, **kwargs) -> ObjectId:
        """
        a PSTAR is a concept in Harvest where objects are stored on five dimensions
        :param database: override
        :param platform: the cloud provider this database was retrieved from (ie AWS, Azure, Google)
        :param service: the provider's service (ie "RDS", "EC2")
        :param type: service's object classification (ie RDS "instance" or EC2 "event")
        :param account: a unique identifier indicating the account or environment level for this service
        :param region: the geographic region name for the objects retrieved from the underlying API call
        :param count: number of records retrieved in the data collection job
        :param start_time: when the data collection job was started
        :param end_time: when the data collection job completed
        :param api_version: version of this software
        :param module: metadata of the collector used to collect the data
        :param errors: provides and error messages
        :return:
        """

        self.connect()

        # no need to replicate this logic everywhere
        kwargs['duration'] = (kwargs['end_time'] - kwargs['start_time']).total_seconds()

        _id = None
        try:
            from datetime import datetime
            _id = self['harvest']['pstar'].insert_one(kwargs).inserted_id

        except Exception as ex:
            logger.error(f'{self._log_prefix}: ' + ' '.join(ex.args))

        finally:
            return _id
