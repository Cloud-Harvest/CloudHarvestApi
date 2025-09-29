from CloudHarvestCoreTasks.blueprints import HarvestApiBlueprint
from flask import Response, request
from logging import getLogger

from CloudHarvestApi.blueprints.home import not_implemented_error

logger = getLogger('harvest')

agents_blueprint = HarvestApiBlueprint(
    'agents_bp', __name__,
    url_prefix='/agents'
)

CACHED_TEMPLATES = {}

@agents_blueprint.route(rule='/get_agent_by_name/<agent_name>', methods=['GET'])
def get_agent_by_name(agent_name: str) -> str | dict:
    """
    Get an agent by its name.

    :param agent_name: The name of the agent to get.
    :return: The agent dictionary if found, else None.
    """

    from CloudHarvestCoreTasks.silos import get_silo
    harvest_nodes = get_silo('harvest-nodes').connect()

    while True:
        cursor = 0
        cursor, batch = harvest_nodes.scan(cursor=cursor, match=f'agent:*', count=100)

        if batch:
            for agent_key in batch:
                cursor_agent_name = harvest_nodes.hget(agent_key, 'name')

                if cursor_agent_name == agent_name:
                    return agent_key

        if cursor == 0:
            return {'error': f'Agent with name `{agent_name}` not found.'}

@agents_blueprint.route(rule='/get_agent_status', methods=['GET'])
def get_agent_status():
    return not_implemented_error()

@agents_blueprint.route(rule='/get_template/<template_category>/<template_name>', methods=['GET'])
def get_agent_template(template_category: str, template_name: str) -> Response:
    """
    Get a template from an agent.

    Arguments
    template_category (str): The category of the template to get.
    template_name (str): The name of the template to get.

    """
    from CloudHarvestApi.blueprints.base import safe_request_get_json

    result = {}
    request_data = safe_request_get_json(request)

    # Check for a valid template name
    if not request_data.get('template_name'):
        return Response({'error': '`template_name` must be provided.'}, 400)


    # Find an agent with this template name
    from CloudHarvestCoreTasks.silos import get_silo
    harvest_nodes = get_silo('harvest-nodes').connect()

    cursor = 0
    agent_id = None

    while agent_id is None:
        cursor = 0
        cursor, batch = harvest_nodes.scan(cursor=cursor, match=f'agent:*', count=100)

        if batch:
            # Check each agent for the template
            for agent_key in batch:
                available_templates = harvest_nodes.hget(agent_key, 'available_templates') or []

                # Break if we find the template on this agent
                if f'template_{template_category}/{template_name}' in available_templates:
                    agent_id = agent_key
                    break

        # Break if we've scanned all agents
        if cursor == 0:
            return Response({'error': f'Agent with template `{template_category}/{template_name}` not found.'}, 400)

    # Request the template from the agent
    from requests import get, RequestException, HTTPError
    from flask import jsonify
    from CloudHarvestCoreTasks.environment import Environment

    max_attempts = 5
    attempts = 0
    result = {}

    while attempts < max_attempts:
        attempts += 1

        try:
            response = get(f'https://{agent_id}/templates/get_template/{request_data.get("template_type")}/{request_data.get("template_name")}',
                           cert=Environment.get('api.connection.pemfile'),
                           timeout=1)

            response.raise_for_status()
            if response.status_code == 200:
                result = response.json()

                if not result:
                    result = {'error': f'Template not found on agent.'}
                break

            else:
                logger.debug(f'get_agent_template: Received status code {response.status_code} from agent {agent_id}. Response: {response.text}')
                result = {'error': f'Agent responded with status code {response.status_code}.'}

        except (HTTPError, RequestException) as e:
            logger.debug(f'get_agent_template: HTTP error when contacting agent {agent_id}: {e}')
            if attempts < max_attempts:
                continue

            else:
                result = {'error': f'HTTP error when contacting agent: {e}'}
                break

    return jsonify(result)

@agents_blueprint.route(rule='/shutdown_agent', methods=['GET'])
def shutdown_agent() -> Response:
    return not_implemented_error()

@agents_blueprint.route(rule='/start_agent_queue', methods=['GET'])
def start_agent():
    return not_implemented_error()

@agents_blueprint.route(rule='/stop_agent_queue', methods=['GET'])
def stop_agent():
    return not_implemented_error()
