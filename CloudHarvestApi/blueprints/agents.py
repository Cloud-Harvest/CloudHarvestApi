from blueprints.base import HarvestBlueprint
from flask import Response, jsonify
from logging import getLogger

logger = getLogger('harvest')

agents_blueprint = HarvestBlueprint(
    'agents_bp', __name__
)

@agents_blueprint.route(rule='shutdown', methods=['GET'])
def shutdown() -> Response:
    pass

@agents_blueprint.route(rule='start', methods=['GET'])
def start():
    pass

@agents_blueprint.route(rule='status', methods=['GET'])
def status():
    pass

@agents_blueprint.route(rule='stop', methods=['GET'])
def stop():
    pass
