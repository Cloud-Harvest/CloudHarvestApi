from CloudHarvestCoreTasks.blueprints import HarvestApiBlueprint
from flask import Response
from logging import getLogger

from CloudHarvestApi.blueprints.home import not_implemented_error
from CloudHarvestApi.blueprints.base import safe_jsonify

logger = getLogger('harvest')

plugins_blueprint = HarvestApiBlueprint(
    'plugins_bp', __name__,
    url_prefix='/plugins'
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

    from CloudHarvestCoreTasks.environment import Environment
    return safe_jsonify(
        success=True,
        reason='OK',
        result=Environment.get('plugins') or []
    )
