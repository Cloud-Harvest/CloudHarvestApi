from CloudHarvestCoreTasks.blueprints import HarvestApiBlueprint
from flask import Response, jsonify, request


silos_blueprint = HarvestApiBlueprint(
    'silos_bp', __name__,
    url_prefix='/silos'
)

@silos_blueprint.route(rule='/get', methods=['GET'])
def get_silos() -> Response:
    from app import CloudHarvestNode

    result = CloudHarvestNode.config.get('silos', {})

    return jsonify(result)

@silos_blueprint.route(rule='/list', methods=['GET'])
def list_silos() -> Response:
    from app import CloudHarvestNode

    result = list(CloudHarvestNode.config.get('silos', {}).keys())

    return jsonify(result)
