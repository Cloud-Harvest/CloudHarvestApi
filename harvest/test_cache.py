import pytest
from cache import HarvestCacheConnection
from startup import load_configuration_files, load_cache_connections

api_configuration = load_configuration_files()
cache_nodes = load_cache_connections(cache_config=api_configuration['cache'])


def test_connection():
    assert cache_nodes[0].is_connected


def test_add_indexes():
    indexes = api_configuration['cache']['indexes']

    cache_nodes[0].add_indexes(indexes=indexes)


def test_set_pstar():
    from json import load

    with open('test_data/cache_pstar.json', 'r') as test_data:
        test_file = load(test_data)

    cache_nodes[0].set_pstar(**test_file)
