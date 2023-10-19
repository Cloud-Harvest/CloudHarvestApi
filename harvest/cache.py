"""
cache.py - defines api-specific operations used for communicating with the backend cache
"""

from bson import ObjectId
from datetime import datetime, timezone
from logging import getLogger
from pymongo import MongoClient
logger = getLogger('harvest')
_flat_record_separator = '.'


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
            for collection in indexes['harvest'].keys():
                # identify indexes
                for index in indexes['harvest'][collection]:
                    if isinstance(index, (str or list)):
                        self['harvest'][collection].create_index(keys=index)
                        logger.debug(f'{self._log_prefix}: added index: {database}.{collection}.{str(index)}')

                    elif isinstance(index, dict):
                        # pymongo is very picky and demands a list[tuple())
                        keys = [(i['field'], i.get('sort', 1)) for i in index.get('keys', [])]

                        self['harvest'][collection].create_index(keys=keys, **index['options'])

                        logger.debug(f'{self._log_prefix}: added index: {database}.{collection}.{str(index)}')

                    else:
                        logger.error(f'unexpected type for index `{index}`: {str(type(index))}')

    @staticmethod
    def check_harvest_metadata(flat_record: dict) -> bool:
        if not flat_record:
            return False

        required_fields = ('Platform',
                           'Service',
                           'Type',
                           'Account',
                           'Region',
                           'Module.FilterCriteria.0',       # FilterCriteria requires at least one value, so .0 is expected
                           'Module.Name',
                           'Module.Repository',
                           'Module.Version',
                           'Dates.DeactivatedOn',
                           'Dates.FirstSeen',
                           'Dates.LastSeen',
                           'Active')

        for field in required_fields:
            field_name = _flat_record_separator.join(['Harvest', field])

            if field_name not in flat_record.keys():
                logger.warning('record failed harvest metadata check: ' + field_name)
                return False

        return True

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

    def deactivate_records(self, collection_name: str, record_ids: list) -> dict:
        collection = self['harvest'][collection_name]

        # deactivate records which were not inserted/updated in this write operation
        records_to_deactivate = [r["_id"] for r in collection.find({"Harvest.Active": True, "_id": {"$nin": record_ids}},
                                                                   {"_id": 1})]

        update_set = {"$set": {"Harvest.Active": False,
                               "Harvest.Dates.DeactivatedOn": datetime.now(tz=timezone.utc)}}

        update_many = collection.update_many(filter={"_id": {"$in": records_to_deactivate}},
                                             update=update_set)

        # update the meta cache
        collection = self['harvest']['meta']
        update_meta = collection.update_many(filter={"Collection": collection_name,
                                                     "CollectionId": {"$in": records_to_deactivate}},
                                             update=update_set)

        logger.debug(f'{self._log_prefix}: harvest.{collection_name}: deactivated {update_many.modified_count}')

        return {
            'deactivated_ids': records_to_deactivate,
            'modified_count': update_many.modified_count,
            'meta_count': update_meta.modified_count
        }

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

    @staticmethod
    def get_unique_filter(record: dict, flat_record: dict) -> dict:
        """
        retrieves the unique identifier defined by the module for this record
        :param record: original record
        :param flat_record: flattened record
        :return: a new dict of field: fieldValue
        """
        return {field: flat_record.get(field) for field in record['Harvest']['Module']['FilterCriteria']}

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

    def set_pstar(self, **kwargs) -> ObjectId:
        """
        a PSTAR is a concept in Harvest where objects are stored on five dimensions
        ['harvest'][platform.service.type]
        :param Platform: the cloud provider this database was retrieved from (ie AWS, Azure, Google)
        :param Service: the provider's service (ie "RDS", "EC2")
        :param Type: service's object classification (ie RDS "instance" or EC2 "event")
        :param Account: a unique identifier indicating the account or environment level for this service
        :param Region: the geographic region name for the objects retrieved from the underlying API call
        :param Count: number of records retrieved in the data collection job
        :param StartTime: when the data collection job was started
        :param EndTime: when the data collection job completed
        :param ApiVersion: version of this software
        :param Module: metadata of the collector used to collect the data
        :param Errors: provides and error messages
        :return:
        """

        self.connect()

        # no need to replicate this logic everywhere
        kwargs['duration'] = self.duration_in_seconds(a=kwargs['EndTime'], b=kwargs['StartTime'])

        _id = None
        try:
            from datetime import datetime
            _id = self['harvest']['pstar'].find_one_and_update(filter={k: kwargs.get(k) for k in ['Platform',
                                                                                                  'Service',
                                                                                                  'Type',
                                                                                                  'Account',
                                                                                                  'Region']},
                                                               projection={'_id': 1},
                                                               update={"$set": kwargs},
                                                               upsert=True).get('_id')

        except Exception as ex:
            logger.error(f'{self._log_prefix}: ' + ' '.join(ex.args))

        finally:
            return _id

    def write_record(self, record: dict, meta_extra_fields: tuple = ()) -> dict:
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
                "FilterCriteria": list
            },
            "Dates": {
                "FirstSeen": datetime.datetime,
                "LastSeen": datetime.datetime,
                "DeactivatedOn": datetime.datetime,
            },
            "Active": bool
        }
        :param record: a dictionary object representing a single record
        :param meta_extra_fields: extra fields to add to the meta collection
        :return: _id
        """

        # should be a new or existing ObjectId
        result = None

        from flatten_json import flatten
        flat_record = flatten(record, separator=_flat_record_separator)

        # only write a record if there is a metadata object - otherwise kill it
        if self.check_harvest_metadata(flat_record=flat_record):

            collection_name = self.get_collection_name(**record['Harvest'])
            collection = self['harvest'][collection_name]

            record['Harvest']['Module']['UniqueFilter'] = self.get_unique_filter(record=record,
                                                                                 flat_record=flat_record)

            existing_record = collection.find_one(record['Harvest']['Module']['UniqueFilter'],
                                                  {'_id': 1, 'Harvest': 1})

            # if there is an existing record, write data to it
            if existing_record:
                _id = existing_record['_id']
                # update new record metadata with existing record's data
                record['Harvest']['Active'] = True
                record['Harvest']['Dates']['FirstSeen'] = existing_record['Harvest']['Dates']['FirstSeen']

                collection.update_one(filter={"_id": existing_record['_id']},
                                      update={"$set": record})

            # no record exists
            else:
                _id = collection.insert_one(record).inserted_id

            # return an _id and collection
            result = {'_id': _id, 'collection': collection_name}

            # write metadata

            # the uniqueness of a given record is based on Collection and CollectionId
            meta_filter = {"Collection": collection_name, "CollectionId": _id}

            # the meta record is the metadata filter, Harvest component, and any extra fields defined by the caller
            meta_record = {
                **meta_filter,
                "Harvest": record["Harvest"],
                **{k: record.get(k) or flat_record.get(k) for k in meta_extra_fields}
            }

            # add the record based on the meta filter
            meta = self['harvest']['meta'].update_one(filter=meta_filter,
                                                      update={"$set": meta_record},
                                                      upsert=True).upserted_id

            # include the meta record id in the results
            result['meta_id'] = meta

        else:
            from pprint import pformat
            logger.warning(f'{self._log_prefix}: failed to write record to cache - missing metadata')
            logger.debug(pformat(record))

        return result

    def write_records(self, records: list) -> list:
        """
        top-level co
        :param records:
        :return:
        """

        # gather record _ids by inserting/updating records
        updated_records = []
        for record in records:
            write_attempt = self.write_record(record=record)
            if write_attempt:
                updated_records.append(write_attempt)

        return updated_records


class HarvestCacheHeartBeatThread:
    def __init__(self, writer: HarvestCacheConnection, version: str):
        self._version = version
        self._writer = writer

        from threading import Thread
        self.thread = Thread(target=self._run, name='cache_heartbeat', daemon=True)

        self.thread.start()

    def _run(self):
        import platform
        from socket import getfqdn
        from time import sleep
        from datetime import datetime, timezone

        start_datetime = datetime.now(tz=timezone.utc)

        while True:
            self._writer.connect()

            self._writer['harvest']['api_nodes'].update_one(filter={"hostname": getfqdn()},
                                                            upsert=True,
                                                            update={"$set": {"hostname": getfqdn(),
                                                                             "os": platform.system(),
                                                                             "version": self._version,
                                                                             "start": start_datetime,
                                                                             "last": datetime.now(tz=timezone.utc)
                                                                             }
                                                                    }
                                                            )

            sleep(1)
