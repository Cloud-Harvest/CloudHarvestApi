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

    with open('harvest/test_data/cache_pstar.json', 'r') as test_data:
        test_file = load(test_data)

    from dateutil.parser import parse
    test_file['start_time'] = parse(test_file['start_time'])
    test_file['end_time'] = parse(test_file['end_time'])

    _id = cache_nodes['writer'].set_pstar(**test_file)

    assert _id

    result = cache_nodes['writer']['harvest']['pstar'].find_one({'_id': _id}, {'_id': 0})

    assert result == test_file

    # delete the test record
    cache_nodes['writer']['harvest']['pstar'].delete_one(_id)
