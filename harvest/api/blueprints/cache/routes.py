from flask import Blueprint, Response, jsonify, request
from json import loads

# Blueprint Configuration
blueprint = Blueprint(
    'cache_bp', __name__
)


@blueprint.route('/cache/collect', methods=['GET'])
def cache_collect(platform: str, service: str, type: str, account: str, region: str) -> Response:
    pass


@blueprint.route('/cache/map', methods=['GET'])
def cache_map(platform: str, service: str, type: str, account: str, region: str) -> Response:
    pass


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
