"""
cache.py - defines api-specific operations used for communicating with the backend cache
"""
from datetime import datetime

import pymongo.collection
from bson import ObjectId
from pymongo import MongoClient
from logging import getLogger
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

    @staticmethod
    def get_unique_filter(record: dict, flat_record: dict) -> dict:
        """
        retrieves the unique identifier defined by the module for this record
        :param record: original record
        :param flat_record: flattened record
        :return: a new dict of field: fieldValue
        """
        return {field: flat_record.get(field) for field in record['Harvest']['Module']['FilterCriteria']}

    def write_record(self, database: str, record: dict, meta_extra_fields: tuple = ()) -> dict:
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
        :param database: target database for records to be written to
        :param record: a dictionary object representing a single record
        :param meta_extra_fields: extra fields to add to the meta collection
        :return: _id
        """

        # should be a new or existing ObjectId
        result = None

        from flatten_json import flatten, unflatten_list
        flat_record = flatten(record, separator=_flat_record_separator)

        # only write a record if there is a metadata object - otherwise kill it
        if self.check_harvest_metadata(flat_record=flat_record):

            collection_name = self.get_collection_name(**record['Harvest'])
            collection = self[database][collection_name]

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

            meta = self[database]['meta'].update_one(filter=meta_filter,
                                                     update={"$set": meta_record},
                                                     upsert=True).upserted_id

            result['meta_id'] = meta

        else:
            from pprint import pprint
            logger.warning(f'{self._log_prefix}: failed to write record to cache - missing metadata')
            logger.debug(pprint(record))

        return result

    def write_records(self, database: str, records: list) -> list:
        from datetime import datetime

        # gather record _ids by inserting/updating records
        updated_records = []
        for record in records:
            write_attempt = self.write_record(database=database, record=record)
            if write_attempt:
                updated_records.append(write_attempt)

        return updated_records

    def deactivate_records(self, database: str, collection_name: str, record_ids: list) -> dict:
        collection = self[database][collection_name]

        # deactivate records which were not inserted/updated in this write operation
        records_to_deactivate = [r["_id"] for r in collection.find({"Harvest.Active": True, "_id": {"$nin": record_ids}},
                                                                   {"_id": 1})]

        update_set = {"$set": {"Harvest.Active": False,
                               "Harvest.Dates.DeactivatedOn": datetime.utcnow()}}

        update_many = collection.update_many(filter={"_id": {"$in": records_to_deactivate}},
                                             update=update_set)

        # update the meta cache
        collection = self[database]['meta']
        update_meta = collection.update_many(filter={"Collection": collection_name,
                                                     "CollectionId": {"$in": records_to_deactivate}},
                                             update=update_set)

        logger.debug(f'{self._log_prefix}: {database}.{collection_name}: deactivated {update_many.modified_count}')

        return {
            'deactivated_ids': records_to_deactivate,
            'modified_count': update_many.modified_count,
            'meta_count': update_meta.modified_count
        }

    # def write_metadata_cache(self, database: str, record: dict, extra_fields: tuple = ()) -> ObjectId:
    #     """
    #     the meta collection contains all records written to the Harvest backend database
    #     :param database: name of the database to write to (usually 'harvest')
    #     :param record: a record to write to the database
    #     :param extra_fields: additional fields which may be added to the meta cache (ie Tags)
    #     :return:
    #     """
    #
    #     collection = self[database]['meta']
    #     filter_criteria = self.make_filter_criteria(record=record)
    #
    #     # we'll only add extra fields if they are defined
    #     if extra_fields:
    #         # when an extra field contains a period, we treat it as a sub-object
    #         # therefore we flatten the record and add the values to the filter_criteria
    #         if any(['.' in x for x in extra_fields]):
    #             from flatten_json import flatten, unflatten_list
    #             flat_record = flatten(record, separator=_flat_record_separator)
    #
    #             # add the objects to the filter_criteria
    #             meta = {x: flat_record.get(x) for x in extra_fields}
    #
    #             # add the filter_criteria back to the Harvest object
    #             meta['Harvest.filter_criteria'] = flatten(filter_criteria, separator=_flat_record_separator)
    #
    #             # return the object to its original state
    #             meta = unflatten_list(meta, separator=_flat_record_separator)
    #
    #         else:
    #             # these filter_criteria
    #             meta = {x: record.get(x) for x in filter_criteria}
    #
    #     else:
    #         meta = record
    #
    #     _id = self.upsert(database=database,
    #                       collection_name=collection.name,
    #                       filter_criteria=filter_criteria,
    #                       record=meta)

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
