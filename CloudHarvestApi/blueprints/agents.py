from CloudHarvestCoreTasks.blueprints import HarvestApiBlueprint
from flask import Response, jsonify
from logging import getLogger

from .home import not_implemented_error

logger = getLogger('harvest')

agents_blueprint = HarvestApiBlueprint(
    'agents_bp', __name__,
    url_prefix='/agents'
)

@agents_blueprint.route(rule='/shutdown', methods=['GET'])
def shutdown() -> Response:
    return not_implemented_error()

@agents_blueprint.route(rule='/start', methods=['GET'])
def start():
    return not_implemented_error()

@agents_blueprint.route(rule='/status', methods=['GET'])
def status():
    return not_implemented_error()

@agents_blueprint.route(rule='/stop', methods=['GET'])
def stop():
    return not_implemented_error()
