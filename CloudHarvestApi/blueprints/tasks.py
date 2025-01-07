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

@tasks_blueprint.route(rule='/get_task_results/<task_chain_id>', methods=['GET'])
def get_task_results(task_chain_id: str) -> Response:
    """
    Returns the results of a task chain.
    Args:
        task_chain_id: A task chain ID (uuid4)

    Returns:
        A response with the task chain results.
    """

    from CloudHarvestCoreTasks.silos import get_silo
    silo = get_silo('harvest-task-results')

    reason = 'OK'
    results = {}

    try:
        client = silo.connect()
        results = client.get(task_chain_id)

    except Exception as ex:
        reason = f'Failed to get task results with error: {str(ex)}'
        logger.error(reason)

    finally:
        return jsonify({
            'success': reason == 'OK',
            'reason': reason,
            'result': results
        })


@tasks_blueprint.route(rule='/list_task_results', methods=['GET'])
def list_task_results() -> Response:
    """
    Lists all task results.
    :return: A response.
    """

    from CloudHarvestCoreTasks.silos import get_silo
    silo = get_silo('harvest-task-results')

    reason = 'OK'
    results = []

    try:
        client = silo.connect()

        results = client.keys() or []

    except Exception as ex:
        reason = f'Failed to list task results with error: {str(ex)}'
        logger.error(reason)

    finally:
        return jsonify({
            'success': reason == 'OK',
            'reason': reason,
            'result': results
        })


@tasks_blueprint.route(rule='/list', methods=['GET'])
def list_tasks() -> Response:
    """
    Lists all tasks.
    :return: A response.
    """

    silo_names = ('harvest-task-queue', 'harvest-tasks', 'harvest-task-results')

    from CloudHarvestCoreTasks.silos import get_silo

    results = []
    for silo_name in silo_names:
        client = get_silo(silo_name).connect()
        keys = client.keys()

        for key in keys:
            results.append({'silo': silo_name, 'task_chain_id': key})

    return jsonify({
        'success': True,
        'result': results
    })


@tasks_blueprint.route(rule='/escalate/<task_id>', methods=['GET'])
def escalate_task(task_id: str) -> Response:
    """
    Removes a task from the global task queue and adds uses the /agents/inject endpoint to
    add the task to the agent queue directly.
    :param task_id: The task ID.
    :return: A response.
    """
    return not_implemented_error()


@tasks_blueprint.route(rule='/queue/<priority>/<task_category>/<task_name>', methods=['POST'])
def queue_task(priority: int, task_category: str, task_name: str) -> Response:
    """
    Queues a task.

    Arguments
    ---------
    priority: (int) The priority of the task. Lower numbers are higher priority.
    task_category: (str) The name of the task. Typically, 'report' or 'service'.
    task_model_name: (str) The name of the task model. Usually something like 'harvest.nodes'.

    :return: A response.
    """
    from CloudHarvestCorePluginManager import Registry

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
            'priority': priority,
            'name': task_name,
            'category': task_category,
            'model': task_model,
            'config': request.json.get('user_config', {}),
            'created': datetime.now(timezone.utc)
        }

        from json import dumps
        payload = dumps(task, default=str)

        # Create a unique name for the task
        task_redis_name = f"task::{task['id']}"

        try:

            # Create the task queue item
            client.setex(name=task_redis_name, value=payload, time=3600)

            # Now add the task to the queue
            client.rpush(f"queue::{priority}", task_redis_name)

        except Exception as ex:
            reason = f'Failed to queue task {task_name} with error: {str(ex)}'

            # ROlLBACK
            client.delete(name=task_redis_name)
            client.lrem(name=f"queue::{priority}", value=task_redis_name)

        else:
            reason = 'OK'

        result = {
            'success': reason == 'OK',
            'reason': reason,
            'result': {
                'id': task['id'],
                'priority': task['priority'],
                'created': task['created'],
            }
        }

    else:
        result = {
            'success': False,
            'reason': f'TaskChain {task_name} not found',
            'result': {}
        }

    return jsonify(result)
