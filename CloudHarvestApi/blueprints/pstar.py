from CloudHarvestCoreTasks.blueprints import HarvestApiBlueprint
from flask import Response, request
from logging import getLogger

from CloudHarvestApi.blueprints.base import (
    CachedData,
    RedisRequest,
    safe_jsonify,
    use_cache_if_valid,
    safe_request_get_json
)

logger = getLogger('harvest')

pstar_blueprint = HarvestApiBlueprint(
    'pstar_bp', __name__,
    url_prefix='/pstar'
)


CACHED_PLATFORM_REGIONS = CachedData(data=[], valid_age=0)


@pstar_blueprint.route(rule='/list_accounts', methods=['GET'])
def list_accounts() -> Response:
    """
    List the available platforms and accounts by retrieving them from the agent configurations.
    :return: A response.
    """

    from json import loads

    redis_request = RedisRequest('harvest-nodes')
    agents = redis_request.keys('agent*')

    result = []
    message = 'OK'

    try:
        accounts = []
        [
            accounts.extend(loads(redis_request.hget(agent, key='accounts')) or [])
            for agent in agents
        ]

        # Remove duplicates
        accounts = sorted(list(set(accounts)))

        result = [
            {
                'platform': account.split(':')[0], 'account': account.split(':')[1]
            }
            for account in accounts
            if account is not None and ':' in account
        ]

    except Exception as ex:
        message = f'Failed to list available accounts with error: {str(ex)}'

    return safe_jsonify(
        success=True if message == 'OK' else False,
        reason=message,
        result=result
    )


@pstar_blueprint.route(rule='/list_platform_regions/<platform>', methods=['GET'])
@use_cache_if_valid(CACHED_PLATFORM_REGIONS)
def list_platform_regions(platform: str) -> Response:
    from json import loads
    from CloudHarvestApi.blueprints.tasks import await_task, queue_task

    redis_request = RedisRequest('harvest-nodes')
    agents = redis_request.keys('agent*') or []

    accounts = []

    # Scan through the agents until we find one operating on the requested platform
    for agent in agents:
        agent_accounts = [
            account.split(':')[1]
            for account in loads(redis_request.hget(name=agent, key='accounts')) or []
            if account.startswith(platform)
        ]

        if agent_accounts:
            accounts.extend(agent_accounts)

    accounts = sorted(list(set(accounts)))

    # If no agent with an account in that platform is found, we return an empty list
    if not accounts:
        return safe_jsonify(
            success=False,
            reason=f'Platform `{platform}` not found in agent configurations.',
            result={}
        )

    # With an account number retrieved from an agent, we can now queue a task to get the regions
    for account in accounts:
        queue_result = queue_task(
            priority=0,
            task_category='reports',
            task_name=f'{platform}.regions',
            variables={
                'service': 'account',
                'type': 'regions',
                'account': account,
            }
        )

        try:
            chain_id = queue_result.json['result']['id']

        except Exception as ex:
            chain_id = None

        if chain_id:
            # If the task was queued successfully, we wait for it to complete
            task_result = await_task(chain_id).json

            task_result = {
                'success': task_result.get('success'),
                'reason': task_result.get('reason'),
                'result': task_result['result']['data']
            }

        else:
            task_result = queue_result.json

        if task_result['result']:
            return safe_jsonify(**task_result)

        else:
            logger.debug(f'No regions found for {platform} {account}')
            continue

    # If we reach this point, it means no regions were found for the platform
    return safe_jsonify(
        success=False,
        reason=f'No regions found for platform `{platform}`.',
        result={}
    )

@pstar_blueprint.route(rule='/list_platforms', methods=['GET'])
def list_platforms() -> Response:
    """
    List the available platforms by retrieving them from the agent configurations.
    :return: A response.
    """

    from json import loads

    redis_request = RedisRequest('harvest-nodes')
    agents = redis_request.keys('agent*')

    result = []
    message = 'OK'

    try:
        platforms = []
        for agent in agents:
            for platform in loads(redis_request.hget(name=agent, key='accounts')) or []:
                try:
                    p = platform.split(':')[0]
                    if p not in platforms and p is not None:
                        platforms.append(p)

                except Exception as ex:
                    continue

        # Format as a dictionary
        result = [
            {
                'platform': platform
            }
            for platform in platforms
        ]

    except Exception as ex:
        message = f'Failed to list available accounts with error: {str(ex)}'

    return safe_jsonify(
        success=True if message == 'OK' else False,
        reason=message,
        result=result
    )


@pstar_blueprint.route(rule='/list_services', methods=['GET'])
def list_services() -> Response:
    """
    List the available services.

    Returns:
    """

    from CloudHarvestApi.blueprints.tasks import list_available_templates

    services = []
    templates = list_available_templates().json.get('result') or []

    message = 'OK'

    try:
        for template in templates:
            template_category, template_name = template.split('/')
            _, template_category = template_category.split('_')

            if template_category == 'services':
                services.append(template_name)

    except Exception as ex:
        message = f'Failed to list available services with error: {str(ex)}'

    return safe_jsonify(
        success=True if message == 'OK' else False,
        reason=message,
        result=sorted(list(set(services)))
    )


@pstar_blueprint.route(rule='/list_pstar', methods=['GET'])
def list_pstar(platform=None, service=None, type=None, account=None, region=None, **kwargs) -> Response:
    """
    Get the PStar data for a given platform, service, type, account, and region.

    Arguments:
        platform (str): The platform to filter by.
        service (str): The service to filter by.
        type (str): The type to filter by.
        account (str): The account to filter by.
        region (str): The region to filter by.

    Returns:
        Response: A JSON response containing the PStar data.
    """

    results = []
    message = 'OK'

    pstar = format_pstar(safe_request_get_json(request), platform=platform, service=service, type=type, account=account,
                         region=region)

    from re import findall

    try:
        # Get the list of available templates
        services = list_services().json.get('result') or []

        # Return matching platforms
        platforms = [
            p['platform']
            for p in list_platforms().json.get('result') or []
            if findall(pstar['platform'], p['platform'])
        ]

        # Iterate over the PSTAR fields, creating a list of results
        for p in platforms:
            # Get the list of available accounts by platform
            accounts = [
                a['account']
                for a in list_accounts().json.get('result') or []
                if a['platform'] == p and findall(pstar['account'], a['account'])
            ]

            # Get the list of available regions by platform
            regions = [
                r['Region']
                for r in list_platform_regions(p).json.get('result') or []
                if findall(pstar['region'], r['Region'])
            ]

            for a in accounts:
                for r in regions:
                    for s in services:
                        service_platform, s_name, s_type = s.split('.')
                        if service_platform == p:
                            # Check if the service matches the pstar fields
                            if findall(pstar['service'], s_name):
                                # Check if the type matches the pstar fields
                                if findall(pstar['type'], s_type):
                                    # If all PSTAR fields match, append to results
                                    results.append({
                                        'platform': p,
                                        'service': s_name,
                                        'type': s_type,
                                        'account': a,
                                        'region': r,
                                        'template': s
                                    })

    except Exception as ex:
        message = f'Failed to list available services with error: {str(ex)}'

    return safe_jsonify(
        success=True if message == 'OK' else False,
        reason=message,
        result=results
    )

@pstar_blueprint.route(rule='/queue_pstar/<priority>', methods=['POST'])
def queue_pstar(priority: int, platform: str = None, service: str = None, type: str = None, account: str = None, region: str = None) -> Response:
    """
    Arguments
        priority (int): The priority of the task. Lower numbers indicate higher priority, with 0 being the highest.
        platform (str, optional): The platform to filter by.
        service (str, optional): The service to filter by.
        type (str, optional): The type to filter by.
        account (str, optional): The account to filter by.
        region (str, optional): The region to filter by.

    Returns:
        A response object containing a list of tasks which were queued.
    """

    from uuid import uuid4
    parent_id = str(uuid4())

    pstar = format_pstar(safe_request_get_json(request),
                         platform=platform,
                         service=service,
                         type=type,
                         account=account,
                         region=region)

    pstar = list_pstar(**pstar).json.get('result') or []

    from CloudHarvestApi.blueprints.tasks import queue_task
    result = [
        queue_task(
            priority=priority,
            parent=parent_id,
            task_category='services',
            task_name=task['template'],
            platform=task['platform'],
            service=task['service'],
            type=task['type'],
            account=task['account'],
            region=task['region']
        )
        for task in pstar
    ]

    return safe_jsonify(
        success=True,
        reason='OK',
        result={
            'parent': parent_id,
            'tasks': [task.json for task in result]
        }
    )

def format_pstar(request_kwargs: dict,
                   platform: str = None,
                   service: str = None,
                   type: str = None,
                   account: str = None,
                   region: str = None) -> dict:
    """
    Abstract function to handle PStar requests.

    Arguments
        request_kwargs (dict): The request arguments.

    Returns
        dict: A properly formatted PSTAR.
    """

    return {
        'platform': platform or request_kwargs.get('platform') or '.*',
        'service': service or request_kwargs.get('service') or '.*',
        'type': type or request_kwargs.get('type') or '.*',
        'account': account or request_kwargs.get('account') or '.*',
        'region': region or request_kwargs.get('region') or '.*'
    }


