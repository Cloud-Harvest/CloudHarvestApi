import datetime

import pytest
from startup import load_configuration_files, load_cache_connections

api_configuration = load_configuration_files()
cache_nodes = load_cache_connections(cache_config=api_configuration['cache']['hosts'])


def _load_test_records_json():
    return open('tests/data/test_records.json', 'r')


def test_connection():
    assert cache_nodes['writer'].is_connected


def test_add_indexes():
    from cache.data import add_indexes
    indexes = api_configuration['cache']['indexes']

    add_indexes(client_writer=cache_nodes['writer'], indexes=indexes)


def test_set_pstar():
    from json import load

    # load test file
    with open('tests/data/cache_pstar.json', 'r') as test_data:
        test_file = load(test_data)

    # convert strings to datetime
    from dateutil.parser import parse
    test_file['StartTime'] = parse(test_file['StartTime'])
    test_file['EndTime'] = parse(test_file['EndTime'])

    # write the pstar, returning the _id
    from cache.data import set_pstar
    _id = set_pstar(client_writer=cache_nodes['writer'], **test_file)

    # verify we actually wrote a record
    assert _id

    # retrieve the record written as part of the test
    result = cache_nodes['writer']['harvest']['pstar'].find_one({'_id': _id}, {'_id': 0})

    convert_result = {}
    from datetime import datetime, timezone
    for key, value in result.items():
        # add utc info to datetime objects
        if isinstance(value, datetime):
            convert_result[key] = value.replace(tzinfo=timezone.utc)

        # skip keys created during pstar entry
        elif key in ['duration']:
            pass

        else:
            convert_result[key] = value

    # results minus the 'duration' field
    assert convert_result == test_file


def test_duration_in_seconds():
    from datetime import datetime
    from cache.data import duration_in_seconds

    a = datetime(year=2023, month=1, day=1, hour=23, minute=30, second=0)
    b = datetime(year=2023, month=1, day=2, hour=0, minute=0, second=0)

    assert duration_in_seconds(a=a, b=b) == 1800 or 1800.0


def test_get_collection_name():
    from json import load
    test_json = load(_load_test_records_json())

    from cache.data import get_collection_name
    for record in test_json:
        if record.get('Harvest'):
            assert get_collection_name(client_writer=cache_nodes['writer'],
                                       **record['Harvest']) == 'test_platform.test_service.test_type'


def test_check_harvest_meta():
    from cache.data import _flat_record_separator, check_harvest_metadata
    from json import load
    test_json = load(_load_test_records_json())

    from flatten_json import flatten

    for record in test_json:
        flat_record = flatten(record, separator=_flat_record_separator)

        assert check_harvest_metadata(flat_record=flat_record) == record['expected_state']


def test_write_record():
    # testing changes made to LastSeen
    now = datetime.datetime(year=2023, month=4, day=26, hour=19, minute=44, second=25)

    from json import load
    test_json = load(_load_test_records_json())

    from cache.data import get_collection_name, write_record
    # here we're checking that files are written/aborted as expected
    for original_record in test_json:
        if original_record.get('Harvest'):

            # we do this to force an update (and this will happen with every record update anyway)
            original_record['Harvest']['Dates']['LastSeen'] = now

            collection_name = get_collection_name(**original_record['Harvest'])
            collection = cache_nodes['reader']['harvest'][collection_name]

            record_result = write_record(client_writer=cache_nodes['writer'], record=original_record)

            assert bool(record_result) is original_record['expected_state']

            if record_result:
                new_record = collection.find_one({"_id": record_result['_id']}, {"_id": 0})

                from flatten_json import flatten

                new_record = flatten(new_record, separator='.')
                original_record = flatten(original_record, separator='.')

                # we expect every field except Dates.LastSeen to be the same
                for key, value in new_record.items():
                    if key == 'Dates.LastSeen':
                        assert value.replace(tzinfo=None) == now

                    else:
                        assert value == original_record[key]


def test_write_records():
    from json import load
    test_json = load(_load_test_records_json())

    from cache.data import write_records
    written_records = write_records(client_writer=cache_nodes['writer'], records=test_json)

    assert len(written_records) == len([record for record in test_json if record['expected_state']])

    for record in written_records:
        assert tuple(record.keys()) == ('_id',
                                        'collection',
                                        'meta_id')


def test_deactivate_records():
    # write test records
    from cache.data import deactivate_records, write_records
    from json import load
    test_json = load(_load_test_records_json())

    written_records = write_records(client_writer=cache_nodes['writer'], records=test_json)

    collection = cache_nodes['writer']['harvest'][written_records[0]['collection']]

    collection.insert_one({'test_record': 'deactivate', 'Harvest': {'Active': True}})

    results = deactivate_records(client_writer=cache_nodes['writer'],
                                 collection_name=written_records[0]['collection'],
                                 record_ids=[i['_id'] for i in written_records])

    assert len(results['deactivated_ids']) == results['modified_count']
    assert written_records[0]["_id"] not in results['deactivated_ids']

    assert tuple(results.keys()) == ('deactivated_ids',
                                     'modified_count',
                                     'meta_count')
