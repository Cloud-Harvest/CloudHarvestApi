from blueprints.base import HarvestBlueprint
from flask import Response, jsonify, request
from json import loads

# Blueprint Configuration
persistent_cache_blueprint = HarvestBlueprint(
    'cache_bp', __name__,
    url_prefix='/persistent_silo'
)


@persistent_cache_blueprint.route(rule='collect', methods=['GET'])
def cache_collect() -> Response:
    request_json = loads(request.get_json())
    pass


@persistent_cache_blueprint.route(rule='map', methods=['GET'])
def cache_map() -> Response:
    """
    This endpoint is used to map the data in a collection. It accomplishes this by retrieving all matching records,
    determining their collective structure, and returning that structure to the user.
    """

    request_json = loads(request.get_json())

    from configuration import HarvestConfiguration
    from CloudHarvestCoreTasks.silos.persistent import connect, get_collection_name, map_dicts
    from datetime import datetime, timezone

    start = datetime.now(tz=timezone.utc)

    # identify the target collection based on the platform, service, type, account, and region
    collection_name = get_collection_name(**{
        'Platform': request_json.get('platform'),
        'Service': request_json.get('service'),
        'Type': request_json.get('type'),
    })

    # check if the collection exists
    connection = connect(**HarvestConfiguration.silos['persistent'])
    collection = connection['harvest'][collection_name]

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


@persistent_cache_blueprint.route(rule='upload', methods=['POST'])
def cache_upload() -> Response:
    """

    :return:
    """
    try:
        data = loads(request.get_json())

    except Exception as ex:
        return jsonify(400, f'Could not load json: {ex}')

    else:
        from CloudHarvestCoreTasks.silos.persistent import connect, write_records
        from configuration import HarvestConfiguration
        results = write_records(records=data)

        return jsonify(len(results))


@persistent_cache_blueprint.route(rule='get/data_collections', methods=['GET'])
def cache_get_platforms() -> Response:
    """
    This endpoint is used to retrieve a list of all collections in the persistent silo.
    """
    from CloudHarvestCoreTasks.silos.persistent import connect
    client = connect()
    results = client['harvest'].list_collection_names()

    return jsonify([
        r
        for r in results
        if '.' in r
    ])
