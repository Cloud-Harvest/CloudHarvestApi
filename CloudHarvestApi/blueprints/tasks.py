from CloudHarvestCoreTasks.blueprints import HarvestApiBlueprint
from flask import Response, jsonify, request
from logging import getLogger

from .base import safe_request_get_json
from .home import not_implemented_error

logger = getLogger('harvest')

tasks_blueprint = HarvestApiBlueprint(
    'tasks_bp', __name__,
    url_prefix='/tasks'
)

@tasks_blueprint.route(rule='list', methods=['GET'])
def list() -> Response:
    """
    Lists all tasks.
    :return: A response.
    """
    return not_implemented_error()


@tasks_blueprint.route(rule='escalate/<task_id>', methods=['GET'])
def escalate(task_id: str) -> Response:
    """
    Escalates a task to the highest priority.
    :param task_id: The task ID.
    :return: A response.
    """
    return not_implemented_error()


@tasks_blueprint.route(rule='queue/{task_model_name}', methods=['POST'])
def queue(task_model_name: str) -> Response:
    """
    Queues a task.
    :return: A response.
    """
    from CloudHarvestCorePluginManager.registry import Registry
    request_json = safe_request_get_json(request)

    task_model = Registry.find(name=task_model_name, category='model')

    return not_implemented_error()
