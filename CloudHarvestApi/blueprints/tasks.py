from CloudHarvestCoreTasks.blueprints import HarvestApiBlueprint
from flask import Response, request
from logging import getLogger

from CloudHarvestApi.blueprints.base import CachedData, safe_jsonify, use_cache_if_valid
from CloudHarvestApi.blueprints.home import not_implemented_error

logger = getLogger('harvest')

tasks_blueprint = HarvestApiBlueprint(
    'tasks_bp', __name__,
    url_prefix='/tasks'
)

CACHED_TEMPLATES = CachedData(data=[], valid_age=0)


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

        if client.exists(task_chain_id):
            results = client.hgetall(name=task_chain_id)

        else:
            reason = 'NOT FOUND'

        # Deserialize the results
        from json import loads
        for key, value in results.items():
            results[key] = loads(value)

    except Exception as ex:
        reason = f'Failed to get task results with error: {str(ex)}'
        logger.error(reason)

    finally:
        return safe_jsonify(
            success=reason == 'OK',
            reason=reason,
            result=results
        )

# @tasks_blueprint.route(rule='/list_available_tasks/<task_type>', methods=['GET'])
# def list_available_tasks(task_type: Literal['reports', 'services']) -> Response:
#     """
#     List the tasks available in the system.
#
#     Returns: A list of task models.
#     """
#
#     if task_type not in ('reports', 'services'):
#         return safe_jsonify(success=False, reason=f'Invalid task type: {task_type}', result=[])
#
#     from CloudHarvestCorePluginManager import Registry
#
#     task_models = Registry.find(category=f'template_{task_type}', result_key='*', limit=None)
#
#     result = {
#             'data': [
#                 {
#                     'Name': model['name'],
#                     'Description': model['cls'][list(model['cls'].keys())[0]].get('description', 'Description not provided.'),
#                     'Tags': ', '.join(model.get('tags', []))
#                 } for model in task_models
#             ],
#             'meta': {
#                 'headers': ['Name', 'Tags', 'Description'],
#             },
#         }
#
#     return safe_jsonify(
#         success=True,
#         reason='OK',
#         result=result
#     )

@tasks_blueprint.route(rule='/list_available_templates', methods=['GET'])
@use_cache_if_valid(CACHED_TEMPLATES)
def list_available_templates() -> Response:
    """
    List the available task templates.
    :return: A response.
    """

    from json import loads
    from CloudHarvestCoreTasks.silos import get_silo
    silo = get_silo('harvest-nodes')

    client = silo.connect()

    agents = client.keys('agent*')

    reason = 'OK'
    results = []

    try:
        for agent in agents:

            agent_data = loads(client.get(name=agent))
            agent_templates = agent_data.get('available_templates') or []

            if isinstance(agent_templates, list):
                results.extend(agent_templates)

    except Exception as ex:
        reason = f'Failed to list task results with error: {str(ex)}'
        logger.error(reason)

    finally:
        results = sorted(list(set(results)))
        CACHED_TEMPLATES.update(data=results, valid_age=300)

        return safe_jsonify(
            success=True,
            reason=reason,
            result=results
        )

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
        return safe_jsonify(success=reason == 'OK', reason=reason, result=results)


@tasks_blueprint.route(rule='/list_task_queue', methods=['GET'])
def list_task_queue() -> Response:
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

    return safe_jsonify(
        success=True,
        reason='OK',
        result=results
    )

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
            'config': dict(request.json),
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

    return safe_jsonify(
        success=result['success'],
        reason=result['reason'],
        result=result['result'],
        default={}
    )
