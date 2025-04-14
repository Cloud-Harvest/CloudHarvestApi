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

@home_blueprint.route('/favicon.ico')
def favicon():
    """
    The favicon endpoint.
    :return: No content
    """
    return '', 204

def not_implemented_error() -> Response:
    return jsonify({
        'success': False,
        'message': 'Not implemented.'
    })
