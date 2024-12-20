from CloudHarvestCoreTasks.blueprints import HarvestApiBlueprint
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
    from app import CloudHarvestNode

    result = CloudHarvestNode.config.get('silos', {}).get(silo_name, {})

    return jsonify({
        'success': bool(result),
        'message': f'Silo {silo_name} not found' if not result else 'OK',
        'result': result
    })

@silos_blueprint.route(rule='/list', methods=['GET'])
def list_silos() -> Response:
    from app import CloudHarvestNode

    result = list(CloudHarvestNode.config.get('silos', {}).keys())

    return jsonify({
        'success': bool(result),
        'message': 'No silos found' if not result else 'OK',
        'result': result
    })
