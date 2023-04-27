import datetime

import pytest
from startup import load_configuration_files, load_cache_connections

api_configuration = load_configuration_files()
cache_nodes = load_cache_connections(cache_config=api_configuration['cache']['hosts'])
test_database = 'test'


def _load_test_records_json():
    return open('tests/data/test_records.json', 'r')


def test_connection():
    assert cache_nodes['writer'].is_connected


def test_add_indexes():
    indexes = api_configuration['cache']['indexes']

    cache_nodes['writer'].add_indexes(indexes=indexes)


def test_set_pstar():
    from json import load

    # load test file
    with open('tests/data/cache_pstar.json', 'r') as test_data:
        test_file = load(test_data)

    # convert strings to datetime
    from dateutil.parser import parse
    test_file['start_time'] = parse(test_file['start_time'])
    test_file['end_time'] = parse(test_file['end_time'])

    # write the pstar, returning the _id
    _id = cache_nodes['writer'].set_pstar(**test_file)

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

    # delete the test record
    cache_nodes['writer']['harvest']['pstar'].delete_one({'_id': _id})


def test_duration_in_seconds():
    from datetime import datetime

    a = datetime(year=2023, month=1, day=1, hour=23, minute=30, second=0)
    b = datetime(year=2023, month=1, day=2, hour=0, minute=0, second=0)

    assert cache_nodes['writer'].duration_in_seconds(a=a, b=b) == 1800 or 1800.0


def test_get_collection_name():
    from json import load
    test_json = load(_load_test_records_json())

    for record in test_json:
        if record.get('Harvest'):
            assert cache_nodes['writer'].get_collection_name(**record['Harvest']) == 'test_platform.test_service.test_type'


def test_check_harvest_meta():
    from json import load
    test_json = load(_load_test_records_json())

    for record in test_json:
        assert cache_nodes['writer'].check_harvest_metadata(record.get('Harvest')) == record['expected_state']


def test_write_record():
    # testing changes made to LastSeen
    now = datetime.datetime(year=2023, month=4, day=26, hour=19, minute=44, second=25)

    from json import load
    test_json = load(_load_test_records_json())

    cache = cache_nodes['writer']

    # here we're checking that files are written/aborted as expected
    for original_record in test_json:
        if original_record.get('Harvest'):

            # we do this to force an update (and this will happen with every record update anyway)
            original_record['Harvest']['Dates']['LastSeen'] = now

            collection = cache[test_database][cache.get_collection_name(**original_record['Harvest'])]

            record_result = cache_nodes['writer'].write_record(database=test_database, record=original_record)

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

    cache = cache_nodes['writer']

    written_records = cache.write_records(database=test_database, records=test_json)

    assert len(written_records) == len([record for record in test_json if record['expected_state']])

