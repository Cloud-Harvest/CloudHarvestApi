from flask import Response, jsonify, request
from blueprints.base import HarvestBlueprint
from logging import getLogger

logger = getLogger('harvest')

tasks_blueprint = HarvestBlueprint(
    'tasks_bp', __name__,
    url_prefix='/tasks'
)

@tasks_blueprint.route(rule='list', methods=['GET'])
def list() -> Response:
    """
    Lists all tasks.
    :return: A response.
    """
    pass

@tasks_blueprint.route(rule='escalate/<task_id>', methods=['GET'])
def escalate(task_id: str) -> Response:
    """
    Escalates a task to the highest priority.
    :param task_id: The task ID.
    :return: A response.
    """
    from CloudHarvestCoreTasks.silos import get_silo
    silo = get_silo('harvest-tasks')