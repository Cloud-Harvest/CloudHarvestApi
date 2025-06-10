from CloudHarvestCoreTasks.blueprints import HarvestApiBlueprint
from flask import Response, request
from logging import getLogger

from CloudHarvestApi.blueprints.base import RedisRequest, safe_jsonify, safe_request_get_json, use_cache_if_valid
from CloudHarvestApi.blueprints.home import not_implemented_error
from CloudHarvestCoreTasks.cache import CachedData
from CloudHarvestCoreTasks.tasks.redis import format_hset, unformat_hset

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
        output = get_task_status(task_chain_id=task_chain_id).get_json()
        status = output.get('result', {}).get('status')

        match status:
            case 'complete' | 'error':
                break

            case _:
                sleep(1)

    else:
        return safe_jsonify(
            success=False,
            reason='TIMEOUT',
            result=None
        )

    return get_task_result(task_chain_id=task_chain_id)


@tasks_blueprint.route(rule='/get_task_result/<task_chain_id>', methods=['GET'])
def get_task_result(task_chain_id: str, **kwargs) -> Response:
    """
    Returns the results of a task chain.
    Args:
        task_chain_id: A task chain ID (uuid4)

    Returns:
        A response with the task chain results.
    """
    redis_request = RedisRequest(silo='harvest-tasks')

    reason = 'OK'
    results = {}

    request_json = safe_request_get_json(request)

    try:
        while True:
            cursor, batch = redis_request.scan(cursor=0, match=f'task:*{task_chain_id}*', count=100)

            if batch:
                redis_name = batch[0]
                break

            if cursor == 0:
                redis_name = None
                break

        logger.debug(f'[{task_chain_id}] redis name: {redis_name}')

        if redis_name:
            status = redis_request.hget(name=redis_name, key='status')

            logger.debug(f'[{task_chain_id}] task status: {status}')

            # if the task is not complete, we don't want to return the result
            if status != 'complete':
                results = {
                    'status': status
                }

            else:
                logger.debug(f'[{task_chain_id}] task is complete, fetching results')
                result = redis_request.hgetall(name=redis_name)

                logger.debug(f'[{task_chain_id}] formatting results')
                results = unformat_hset(result)

                if request_json.get('pop'):
                    logger.debug(f'[{task_chain_id}] fetch complete, removing results from cache')
                    # if the task is complete, we want to remove it from the queue
                    redis_request.delete(redis_name)

        else:
            reason = 'NOT FOUND'

    except BaseException as ex:
        from traceback import format_exc
        reason = f'Failed to get task results with error: {str(ex.args)}'
        logger.error(f'{reason}\n{format_exc()}')

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

    result = {}
    reason = 'OK'

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

    def rekey_dict(redis_response: list):
        """
        Rekeys the redis response to a dictionary.
        :param redis_response: The redis response.
        :return: A dictionary with the rekeyed values.
        """
        return {
            key: redis_response[fields.index(key)]
            for key in fields
        }

    try:
        redis_request = RedisRequest(silo='harvest-tasks')

        names = []
        cursor = 0
        while True:
            cursor, batch = redis_request.scan(cursor=int(cursor), match=f'task:*{task_chain_id}*', count=100)

            names.extend(batch)

            if cursor == 0:
                break

        if len(names) == 0:
            reason = 'NOT FOUND'
            return safe_jsonify(
                success=False,
                reason=reason,
                result=result
            )

        elif len(names) == 1:
            result = rekey_dict(unformat_hset(redis_request.hmget(names[0], keys=fields)))

        else:
            # Redis scans yielding multiple results typically happen when a task chain is created from a parent request,
            # such as a `harvest` / `pstar` request. In this case, we need to get the status of each task in the chain.

            all_results = []
            # if there are multiple tasks (as from a parent task), we need to get the status of each task
            for name in names:
                all_results.append(unformat_hset(rekey_dict(redis_request.hmget(name, fields))))

            parent_id = list(set(task['parent'] for task in all_results if task.get('parent')))
            if len(parent_id) == 0:
                parent_id = None
                redis_name = None

            elif len(parent_id) == 1:
                parent_id = parent_id[0]
                redis_name = f'task:{parent_id}'

            else:
                # This should not happen, but we will return a list of parent ids just in case
                redis_name = 'task:' + '/'.join(parent_id)

            def try_aggregate(method, key: str, default=None):
                """
                Tries to aggregate a value from the task results.
                :param method: The aggregation method (min, max, sum).
                :param key: The key to aggregate.
                :param default: The default value if the key is not found.
                :return: The aggregated value.
                """
                try:
                    return method(task.get(key) or default for task in all_results if task.get(key))

                except Exception as ex:
                    return default

            result = {
                'redis_name': redis_name,
                'id': [task['id'] for task in all_results if task.get('id')],
                'parent': parent_id,
                'name': None,
                'type': None,
                'status': 'running' if any(task.get('status') != 'complete' for task in all_results) else 'complete',
                'agent': list(set(task['agent'] for task in all_results if task.get('agent'))),
                'position': len([task.get('status') for task in all_results if task.get('status') == 'complete']),
                'total': len(all_results),
                # 'position': try_aggregate(sum, 'position', 0),
                # 'total': try_aggregate(sum, 'total', 0),
                'start': try_aggregate(min, 'start'),
                'end': try_aggregate(max, 'end')
            }

    except Exception as ex:
        reason = f'Failed to get task status with error: {str(ex)}'
        logger.error(reason)

    return safe_jsonify(
        success=reason == 'OK',
        reason=reason,
        result=result
    )


@use_cache_if_valid(CACHED_TEMPLATES)
@tasks_blueprint.route(rule='/list_available_templates', methods=['GET'])
def list_available_templates() -> Response:
    """
    List the available task templates.
    :return: A response.
    """

    redis_request = RedisRequest(silo='harvest-nodes')

    reason = 'OK'
    results = []

    try:
        agents = redis_request.keys(pattern='agent*')
        for agent in agents:
            agent_templates = unformat_hset(redis_request.hget(name=agent, key='available_templates')) or []
            results.extend(agent_templates)

    except Exception as ex:
        reason = f'Failed to list task results with error: {str(ex)}'
        logger.error(reason)

    results = sorted(list(set(results)))

    # We only cache the templates if we have results
    if results:
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

    reason = 'OK'
    results = []

    try:
        redis_request = RedisRequest(silo='harvest-tasks')

        results = []
        cursor = 0

        # Use SCAN to fetch keys in batches of 100
        while True:
            cursor, batch = redis_request.scan(cursor=cursor, match='task:*', count=100)

            if batch:
                results.extend(batch)

            if cursor == 0:
                break

    except Exception as ex:
        reason = f'Failed to list task results with error: {str(ex)}'
        logger.error(reason)

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
    from datetime import datetime, timezone
    from uuid import uuid4

    incoming_kwargs = (dict(safe_request_get_json(request)) or {}) | kwargs

    task_id = str(uuid4())

    task = {
        'id': task_id,
        'priority': priority,
        'name': task_name,
        'status': 'enqueued',
        'parent': incoming_kwargs.get('parent') or '',
        'category': f'template_{task_category}',
        'config': incoming_kwargs | {'id': task_id},        # must include the task ID in the config otherwise it will not be passed
        'created': datetime.now(timezone.utc)
    }

    # Create a unique name for the task
    redis_name = f"task:{task['parent']}:{task['id']}"
    task['redis_name'] = redis_name

    redis_request = RedisRequest(silo='harvest-tasks')

    try:

        # Create the task queue item
        redis_request.hset(name=redis_name, mapping=format_hset(task))
        redis_request.expire(name=redis_name, time=3600)

        # Now add the task to the queue
        redis_request.rpush(f"queue::{priority}", redis_name)

    except Exception as ex:
        reason = f'Failed to queue task {task_name} with error: {str(ex)}'

        # ROlLBACK
        try:
            redis_request.lrem(name=f"queue::{priority}", value=redis_name)

        except Exception:
            pass

        try:
            redis_request.delete(name=redis_name)

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
