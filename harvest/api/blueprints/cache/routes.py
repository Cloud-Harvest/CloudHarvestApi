from flask import Blueprint, Response, jsonify, request
from typing import List, Literal
from json import loads

# Blueprint Configuration
blueprint = Blueprint(
    'cache_bp', __name__
)


@blueprint.route('/cache/collect', methods=['GET'])
def cache_collect() -> Response:
    request_json = loads(request.get_json())
    pass


@blueprint.route('/cache/map', methods=['GET'])
def cache_map() -> Response:
    request_json = loads(request.get_json())

    from configuration import HarvestConfiguration
    from cache.connection import HarvestCacheConnection
    from cache.data import get_collection_name, map_dicts
    from datetime import datetime, timezone

    start = datetime.now(tz=timezone.utc)

    # identify the target collection based on the platform, service, type, account, and region
    collection_name = get_collection_name(**{
        'Platform': request_json.get('platform'),
        'Service': request_json.get('service'),
        'Type': request_json.get('type'),
    })

    # check if the collection exists
    with HarvestCacheConnection(connect=True, **HarvestConfiguration.cache['connection']) as cache:
        collection = cache['harvest'][collection_name]

        if collection is None:
            return jsonify([{'error': f'collection `{collection_name}` not found.'}])

        elif '.' not in collection_name:
            return jsonify([{'error': f'mapping may only be done on PSTAR collections, not `{collection_name}.`'}])

        data = list(collection.find().limit(50))

    # map the collection
    result = map_dicts(data)

    end = datetime.now(tz=timezone.utc)

    return jsonify({
        'result': result,
        'meta': {
            'start': start,
            'end': end,
            'duration': (end - start).total_seconds(),
            'collection': collection_name,
        }
    })


@blueprint.route('/cache/upload', methods=['POST'])
def cache_upload() -> Response:
    """

    :return:
    """
    try:
        data = loads(request.get_json())

    except Exception as ex:
        return jsonify(400, f'Could not load json: {ex}')

    else:
        from cache.data import HarvestCacheConnection, write_records
        from configuration import HarvestConfiguration
        with HarvestCacheConnection(connect=True, **HarvestConfiguration.cache['connection']) as cache:
            results = write_records(client=cache, records=data)

        return jsonify(len(results))


@blueprint.route('/cache/get/data_collections', methods=['GET'])
def cache_get_platforms() -> Response:
    from cache.connection import HarvestCacheConnection
    from configuration import HarvestConfiguration
    with HarvestCacheConnection(connect=True, **HarvestConfiguration.cache['connection']) as cache:
        results = cache['harvest'].list_collection_names()

    return jsonify([
        r
        for r in results
        if '.' in r
    ])
