from CloudHarvestCoreTasks.blueprints import HarvestApiBlueprint
from flask import Response
from logging import getLogger

from CloudHarvestApi.blueprints.base import CachedData, safe_jsonify, use_cache_if_valid

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

    from CloudHarvestCoreTasks.silos import get_silo
    from json import loads

    silo = get_silo('harvest-nodes')
    client = silo.connect()
    agents = client.keys('agent*')

    result = []
    message = 'OK'

    try:
        accounts = []
        [
            accounts.extend(loads(client.get(agent)).get('accounts') or [])
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

    finally:
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
    from CloudHarvestCoreTasks.silos import get_silo
    silo = get_silo('harvest-nodes')
    client = silo.connect()
    agents = client.keys('agent*') or []

    # Scan through the agents until we find one operating on the requested platform
    for agent in agents:
        agent_data = loads(client.get(name=agent))
        agent_accounts = agent_data.get('accounts') or []

        # Get the account name
        accounts = [
            account
            for account in agent_accounts
            if account.startswith(platform)
        ]

        if accounts:
            account = accounts[0].split(':')[1]
            break

    # If no agent with that platform is found, we return an empty list
    else:
        return safe_jsonify(
            success=False,
            reason=f'Platform `{platform}` not found in agent configurations.',
            result={}
        )

    # With an account number retrieved from an agent, we can now queue a task to get the regions

    queue_result = queue_task(
        priority=0,
        task_category='reports',
        task_name=f'{platform}.regions',
        variables={
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

    return safe_jsonify(**task_result)

@pstar_blueprint.route(rule='/list_platforms', methods=['GET'])
def list_platforms() -> Response:
    """
    List the available platforms by retrieving them from the agent configurations.
    :return: A response.
    """

    from CloudHarvestCoreTasks.silos import get_silo
    from json import loads

    silo = get_silo('harvest-nodes')
    client = silo.connect()
    agents = client.keys('agent*')

    result = []
    message = 'OK'

    try:
        platforms = []
        [
            platforms.extend(loads(client.get(agent)).get('accounts') or [])
            for agent in agents
        ]

        # Remove duplicates
        platforms = sorted(list(set(platforms)))

        result = [
            {
                'platform': platform.split(':')[0]
            }
            for platform in platforms
            if platform is not None and ':' in platform
        ]

    except Exception as ex:
        message = f'Failed to list available accounts with error: {str(ex)}'

    finally:
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
