import pytest
from startup import load_configuration_files, load_cache_connections

api_configuration = load_configuration_files()
cache_nodes = load_cache_connections(cache_config=api_configuration['cache']['hosts'])


def test_connection():
    assert cache_nodes['writer'].is_connected


def test_add_indexes():
    indexes = api_configuration['cache']['indexes']

    cache_nodes['writer'].add_indexes(indexes=indexes)


def test_set_pstar():
    from json import load

    # load test file
    with open('harvest/test_data/cache_pstar.json', 'r') as test_data:
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
