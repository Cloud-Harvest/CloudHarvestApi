"""
cache.py - defines api-specific operations used for communicating with the backend cache
"""
from datetime import datetime

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
        [database][platform.service.type]
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
        kwargs['duration'] = self.duration_in_seconds(a=kwargs['end_time'], b=kwargs['start_time'])

        _id = None
        try:
            from datetime import datetime
            _id = self['harvest']['pstar'].insert_one(kwargs).inserted_id

        except Exception as ex:
            logger.error(f'{self._log_prefix}: ' + ' '.join(ex.args))

        finally:
            return _id

    def write_record(self, database: str, record: dict, filter_criteria: list = None) -> ObjectId:
        """
        a record to be written to the harvest cache
        to qualify as a valid record, it must contain a key named Harvest with the following structure

        "Harvest": {
            "Platform": str,
            "Service": str,
            "Type": str,
            "Account": str,
            "Region": str,
            "Module": {
                "Name": str,
                "Version": str,
                "Repository": str
            },
            "Dates": {
                "FirstSeen": datetime.datetime,
                "LastSeen": datetime.datetime,
                "DeactivatedOn": datetime.datetime,
            },
            "Active": bool
        }
        :param database: the target database name
        :param record: a dictionary object representing a single record
        :param filter_criteria: update records based on these fields (ie DBClusterArn)
        :return: _id
        """

        # should be a new or existing ObjectId
        result = None

        # only write a record if there is a metadata object - otherwise kill it
        if self.check_harvest_metadata(harvest=record.get('Harvest')):
            collection = self[database][self.get_collection_name(**record['Harvest'])]

            # for objects with a unique identifier field, use it to retrieve existing records
            # we need the original object to:
            #  - get original objectId()
            #  - accurately represent the "Dates.FirstSeen" field
            if filter_criteria:
                unique_filter_fields = {k: v for k, v in record.items() if k in filter_criteria}

                existing_record = collection.find_one(unique_filter_fields,
                                                      {'_id': 1, 'Harvest': 1})

                # if there is an existing record, write data to it
                if existing_record:
                    # update new record metadata with existing record's data
                    record['Harvest']['Active'] = True
                    record['Harvest']['Dates']['FirstSeen'] = existing_record['Harvest']['Dates']['FirstSeen']

                    collection.update_one(filter={"_id": existing_record['_id']},
                                          update={"$set": record})

                    result = existing_record['_id']
                # no record exists
                else:
                    result = collection.insert_one(record).inserted_id

            # this object does not have a unique identifier
            else:
                pass
                result = collection.insert_one(record).inserted_id

        else:
            from pprint import pprint
            logger.warning(f'{self._log_prefix}: failed to write record to cache - missing metadata')
            logger.debug(pprint(record))

        return result


    @staticmethod
    def check_harvest_metadata(harvest: dict) -> bool:
        required_fields = ('Platform',
                           'Service',
                           'Type',
                           'Account',
                           'Region',
                           'Module.Name',
                           'Module.Version',
                           'Module.Repository',
                           'Dates.FirstSeen',
                           'Dates.LastSeen',
                           'Dates.DeactivatedOn',
                           'Active')
        try:

            from flatten_json import flatten
            flat_harvest = flatten(harvest, separator='.')

            for field in required_fields:
                assert field in flat_harvest.keys()

        except AssertionError as ae:
            logger.warning('record failed harvest metadata check: ' + ' '.join(ae.args))
            return False

        else:
            return True

    @staticmethod
    def duration_in_seconds(a: datetime, b: datetime) -> int or float:
        """
        a simple, testable function for retrieving the number of seconds between two dates
        :param a: a datetime
        :param b: another datetime
        :return: an integer or float representing the number of seconds between two datetime objects
        """

        return abs((a - b).total_seconds())

    @staticmethod
    def get_collection_name(**harvest_metadata) -> str:
        """
        returns the collection name used in a pstar record write based on the Harvest metadata key
        :param harvest_metadata: the "Harvest": {} key generated by a pstar record write
        :return: str
        """
        return '.'.join((harvest_metadata['Platform'],
                         harvest_metadata['Service'],
                         harvest_metadata['Type']))
