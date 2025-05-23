from CloudHarvestCoreTasks.blueprints import HarvestApiBlueprint
from CloudHarvestCoreTasks.environment import Environment
from flask import Response, jsonify


silos_blueprint = HarvestApiBlueprint(
    'silos_bp', __name__,
    url_prefix='/silos'
)

@silos_blueprint.route(rule='/get/<silo_name>', methods=['GET'])
def get_silo(silo_name: str) -> Response:
    """
    Gets the configuration of a single silo.
    Args:
        silo_name: The name of the silo.

    Returns:
        The configuration of the retrieved silo.
    """
    result = Environment.get('silos', {}).get(silo_name, {})

    return jsonify({
        'success': bool(result),
        'message': f'Silo {silo_name} not found' if not result else 'OK',
        'result': result
    })

@silos_blueprint.route(rule='/get_all', methods=['GET'])
def get_all_silo() -> Response:
    """
    Gets the configuration of all silos registered in the node.
    Returns:
        A dictionary containing the configuration of all silos where the key is the silo name.
    """

    result = Environment.get('silos', {})

    return jsonify({
        'success': bool(result),
        'message': 'No silos found' if not result else 'OK',
        'result': result
    })

@silos_blueprint.route(rule='/list', methods=['GET'])
def list_silos() -> Response:

    result = list(Environment.get('silos', {}).keys())

    return jsonify({
        'success': bool(result),
        'message': 'No silos found' if not result else 'OK',
        'result': result
    })
