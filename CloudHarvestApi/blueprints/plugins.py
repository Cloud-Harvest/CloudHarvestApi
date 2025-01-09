from CloudHarvestCoreTasks.blueprints import HarvestApiBlueprint
from flask import Response, jsonify
from logging import getLogger

from .home import not_implemented_error

logger = getLogger('harvest')

plugins_blueprint = HarvestApiBlueprint(
    'plugins_bp', __name__,
    url_prefix='/agents'
)

@plugins_blueprint.route(rule='/list', methods=['GET'])
def list_all_plugins() -> Response:
    """
    Lists all plugins installed on the API.
    :return: A response of
    >>> {
    >>>     'success': True,
    >>>     'reason': 'OK',
    >>>     'result': ['plugin1', 'plugin2', 'plugin3']
    >>> }
    """

    from app import CloudHarvestNode


    return jsonify({
        'success': True,
        'reason': 'OK',
        'result': CloudHarvestNode.config.get('plugins') or []
    })
