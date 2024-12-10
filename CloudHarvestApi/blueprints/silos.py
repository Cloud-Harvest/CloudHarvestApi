from CloudHarvestCoreTasks.blueprints import HarvestApiBlueprint
from flask import Response, jsonify, request


silos_blueprint = HarvestApiBlueprint(
    'silos_bp', __name__,
    url_prefix='/silos'
)

@silos_blueprint.route(rule='/get', methods=['GET'])
def get_silos() -> Response:
    from app import CloudHarvestApi

    result = CloudHarvestApi.config.get('silos', {})

    return jsonify(result)

@silos_blueprint.route(rule='/list', methods=['GET'])
def list_silos() -> Response:
    from app import CloudHarvestApi

    result = list(CloudHarvestApi.config.get('silos', {}).keys())

    return jsonify(result)
