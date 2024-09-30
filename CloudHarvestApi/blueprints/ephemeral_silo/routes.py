from blueprints.base import HarvestBlueprint
from flask import Response, request
from json import loads

# Blueprint Configuration
ephemeral_cache_blueprint = HarvestBlueprint(
    'cache_bp', __name__,
    url_prefix='/ephemeral_silo'
)


@ephemeral_cache_blueprint.route(rule='collect', methods=['GET'])
def get_jobs() -> Response:
    request_json = loads(request.get_json())
