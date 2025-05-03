from CloudHarvestCoreTasks.blueprints import HarvestApiBlueprint
from flask import Response, request
from logging import getLogger

from CloudHarvestCoreTasks.cache import CachedData
from CloudHarvestCoreTasks.redis import format_hset, unformat_hset
from CloudHarvestApi.blueprints.base import safe_jsonify, safe_request_get_json, use_cache_if_valid
from CloudHarvestApi.blueprints.home import not_implemented_error

logger = getLogger('harvest')

tasks_blueprint = HarvestApiBlueprint(
    'tasks_bp', __name__,
    url_prefix='/tasks'
)

CACHED_TEMPLATES = CachedData(data=[], valid_age=0)


@tasks_blueprint.route(rule='/await/<task_chain_id>', methods=['GET'])
def await_task(task_chain_id: str) -> Response:
    """
    Awaits a task.

    Arguments
    task_chain_id: (str) The task chain ID (uuid4)

    Returns
    A response with the task chain results.
    """

    from datetime import datetime
    from time import sleep

    request_json = safe_request_get_json(request)

    start_time = datetime.now()
    timeout = request_json.get('timeout') or 120

    while (datetime.now() - start_time).total_seconds() < timeout:
        output = get_task_results(task_chain_id=task_chain_id).get_json()
        reason = output.get('reason')

        match reason:
            case 'OK':
                break

            case _:
                sleep(1)

    else:
        return safe_jsonify(
            success=False,
            reason='TIMEOUT',
            result=None
        )

    return get_task_results(task_chain_id=task_chain_id)


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
    silo = get_silo('harvest-tasks')

    reason = 'OK'
    results = {}

    try:
        client = silo.connect()

        redis_name = get_first_task_id(task_chain_id=task_chain_id)

        if redis_name:
            results = client.hget(name=redis_name, key='result') or {}

        else:
            reason = 'NOT FOUND'

        # Deserialize the results
        results = unformat_hset(results)

    except Exception as ex:
        reason = f'Failed to get task results with error: {str(ex)}'
        logger.error(reason)

    finally:
        return safe_jsonify(
            success=reason == 'OK',
            reason=reason,
            result=results
        )

@tasks_blueprint.route(rule='/get_task_status/<task_chain_id>', methods=['GET'])
def get_task_status(task_chain_id: str) -> Response:
    """
    Returns the status of a task chain.
    Args:
        task_chain_id (str): A task chain ID (uuid4)

    Returns:
        A response with the task chain status.
    """

    results = {}
    reason = 'OK'

    try:
        redis_name = get_first_task_id(task_chain_id=task_chain_id)

        from CloudHarvestCoreTasks.silos import get_silo
        silo = get_silo('harvest-tasks')
        client = silo.connect()

        # for status checks, we do not want to return the result as it may be large
        fields = (
            'redis_name',
            'id',
            'parent',
            'name',
            'type',
            'status',
            'agent',
            'position',
            'total',
            'start',
            'end'
        )

        results = unformat_hset(client.hmget(redis_name, fields) or {})

    except Exception as ex:
        reason = f'Failed to get task status with error: {str(ex)}'
        logger.error(reason)

    finally:
        return safe_jsonify(
            success=reason == 'OK',
            reason=reason,
            result=results
        )


# @use_cache_if_valid(CACHED_TEMPLATES)
@tasks_blueprint.route(rule='/list_available_templates', methods=['GET'])
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
            agent_templates = unformat_hset(client.hget(name=agent, key='available_templates')) or []
            results.extend(agent_templates)

    except Exception as ex:
        reason = f'Failed to list task results with error: {str(ex)}'
        logger.error(reason)

    finally:
        results = sorted(list(set(results)))

        # Update the CACHED_TEMPLATES so subsequent calls will be faster
        CACHED_TEMPLATES.update(data=results, valid_age=300)

        return safe_jsonify(
            success=True,
            reason=reason,
            result=results
        )


@tasks_blueprint.route(rule='/list_tasks', methods=['GET'])
def list_tasks() -> Response:
    """
    Lists all task results.
    :return: A response.
    """

    from CloudHarvestCoreTasks.silos import get_silo
    silo = get_silo('harvest-tasks')

    reason = 'OK'
    results = []

    try:
        client = silo.connect()

        results = []
        cursor = '0'

        # Use SCAN to fetch keys in batches of 100
        while cursor != '0':
            cursor, batch = client.scan(cursor=cursor, count=100)
            results.extend(batch)

    except Exception as ex:
        reason = f'Failed to list task results with error: {str(ex)}'
        logger.error(reason)

    finally:
        return safe_jsonify(success=reason == 'OK',
                            reason=reason,
                            result=results)


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
def queue_task(priority: int, task_category: str, task_name: str, *args, **kwargs) -> Response:
    """
    Queues a task.

    Arguments
    ---------
    priority: (int) The priority of the task. Lower numbers are higher priority.
    task_category: (str) The name of the task. Typically, 'report' or 'service'.
    task_model_name: (str) The name of the task model. Usually something like 'harvest.nodes'.

    :return: A response.
    """

    templates = list_available_templates().get_json().get('result')

    template_exists = False
    for template in templates:
        category, name = template.split('/')
        category = category.replace('template_', '')

        if category == task_category and name == task_name:
            template_exists = True
            break


    if not template_exists:
        return safe_jsonify(
            success=False,
            reason=f'TEMPLATE NOT FOUND',
            result=None
        )

    # The task is known to exist on some agent, therefore it can be queued

    from CloudHarvestCoreTasks.silos import get_silo
    silo = get_silo('harvest-tasks')
    client = silo.connect()

    from datetime import datetime, timezone
    from uuid import uuid4

    incoming_kwargs = (dict(safe_request_get_json(request)) or {}) | kwargs

    task = {
        'id': str(uuid4()),
        'priority': priority,
        'name': task_name,
        'status': 'enqueued',
        'parent': incoming_kwargs.get('parent') or '',
        'category': f'template_{task_category}',
        'config': incoming_kwargs,
        'created': datetime.now(timezone.utc)
    }

    # Create a unique name for the task
    redis_name = f"task:{task['parent']}:{task['id']}"
    task['redis_name'] = redis_name

    try:
        # Create the task queue item
        client.hset(name=redis_name, mapping=format_hset(task))
        client.expire(name=redis_name, time=3600)

        # Now add the task to the queue
        client.rpush(f"queue::{priority}", redis_name)

    except Exception as ex:
        reason = f'Failed to queue task {task_name} with error: {str(ex)}'

        # ROlLBACK
        try:
            client.lrem(name=f"queue::{priority}", value=redis_name)

        except Exception:
            pass

        try:
            client.delete(name=redis_name)

        except Exception:
            pass

    else:
        reason = 'OK'

    result = {
        'success': reason == 'OK',
        'reason': reason,
        'result': {
            'redis_name': redis_name,
            'id': task['id'],
            'parent': task['parent'],
            'priority': task['priority'],
            'created': task['created'],
        }
    }

    return safe_jsonify(
        success=result['success'],
        reason=result['reason'],
        result=result['result'],
        default={}
    )

def get_first_task_id(task_chain_id: str) -> str or None:
    """
    Returns the first task ID in a task chain.
    :param task_chain_id: The task chain ID.
    :return: The first task ID.
    """

    from CloudHarvestCoreTasks.silos import get_silo
    silo = get_silo('harvest-tasks')

    client = silo.connect()

    cursor = False

    # Get the first task ID
    while cursor != 0:
        cursor, batch = client.scan(cursor=0, match=f'task:*{task_chain_id}', count=100)

        if batch:
            return batch[0]

    return None
