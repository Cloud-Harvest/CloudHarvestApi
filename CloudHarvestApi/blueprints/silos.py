from CloudHarvestCoreTasks.blueprints import HarvestApiBlueprint
from flask import Response, jsonify, request


silos_blueprint = HarvestApiBlueprint(
    'silos_bp', __name__,
    url_prefix='/silos'
)

@silos_blueprint.route(rule='get', methods=['GET'])
def get() -> Response:
    from ..app import CloudHarvestApi

    return jsonify({
        CloudHarvestApi.config.get('silos', {})
    })

@silos_blueprint.route(rule='list', methods=['GET'])
def list() -> Response:
    from ..app import CloudHarvestApi

    return jsonify({
        CloudHarvestApi.config.get('silos', {}).keys()
    })
