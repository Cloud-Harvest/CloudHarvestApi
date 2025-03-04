from CloudHarvestCoreTasks.blueprints import HarvestApiBlueprint
from flask import Response, jsonify
from logging import getLogger

from CloudHarvestApi.blueprints.home import not_implemented_error

logger = getLogger('harvest')

agents_blueprint = HarvestApiBlueprint(
    'agents_bp', __name__,
    url_prefix='/agents'
)

@agents_blueprint.route(rule='/get_status', methods=['GET'])
def get_agent_status():
    return not_implemented_error()

@agents_blueprint.route(rule='/shutdown', methods=['GET'])
def shutdown_agent() -> Response:
    return not_implemented_error()

@agents_blueprint.route(rule='/start', methods=['GET'])
def start_agent():
    return not_implemented_error()

@agents_blueprint.route(rule='/stop', methods=['GET'])
def stop_agent():
    return not_implemented_error()
