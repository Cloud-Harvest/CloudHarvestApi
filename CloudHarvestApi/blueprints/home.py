from CloudHarvestCoreTasks.blueprints import HarvestApiBlueprint
from flask import Response, jsonify

home_blueprint = HarvestApiBlueprint(
    'home_bp', __name__
)

@home_blueprint.route('/', methods=['GET'])
def home() -> Response:
    return jsonify({
        'message': 'Welcome to the CloudHarvest API.'
    })

def not_implemented_error() -> Response:
    return jsonify({
        'error': 'Not implemented.'
    })
