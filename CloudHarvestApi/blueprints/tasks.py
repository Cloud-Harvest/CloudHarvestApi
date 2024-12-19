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

@tasks_blueprint.route(rule='/list', methods=['GET'])
def list_tasks() -> Response:
    """
    Lists all tasks.
    :return: A response.
    """
    return not_implemented_error()


@tasks_blueprint.route(rule='/escalate/<task_id>', methods=['GET'])
def escalate_task(task_id: str) -> Response:
    """
    Removes a task from the global task queue and adds uses the /agents/inject endpoint to
    add the task to the agent queue directly.
    :param task_id: The task ID.
    :return: A response.
    """
    return not_implemented_error()


@tasks_blueprint.route(rule='/queue/<task_category>/<task_name>/<task_config>', methods=['POST'])
def queue_task(task_category: str, task_name: str, task_config = None) -> Response:
    """
    Queues a task.

    Arguments
    task_category: (str) The name of the task. Typically, 'report' or 'service'.
    task_model_name: (str) The name of the task model. Usually something like 'harvest.nodes'.
    task_config: (dict) Additional configuration of the task.

    :return: A response.
    """
    # TODO: Implement this method and remove the not_implemented_error() call
    # return not_implemented_error()

    from CloudHarvestCorePluginManager import Registry
    # request_json = safe_request_get_json(request)

    task_model = Registry.find(name=task_name, category=f'template_{task_category}', result_key='cls')

    if task_model:
        task_model = task_model[0]

        from CloudHarvestCoreTasks.silos import get_silo
        silo = get_silo('harvest-task-queue')
        client = silo.connect()

        from datetime import datetime, timezone

        from uuid import uuid4

        task = {
            'id': str(uuid4()),
            'name': task_name,
            'category': task_category,
            'model': task_model,
            'config': task_config,
            'created': datetime.now(timezone.utc)
        }

        from json import dumps
        payload = dumps(task, default=str)

        # Store the task in the Redis cache and expire it from the queue after 1 hour
        client.setex(name=task['id'], value=payload, time=3600)

        result = {
            'status': 'success',
            'response': {
                'id': task['id'],
                'created': task['created'],
            }
        }

    else:
        result = {
            'status_code': 500,
            'reason': 'Task not found',
            'response': {}
        }

    return jsonify(result)
