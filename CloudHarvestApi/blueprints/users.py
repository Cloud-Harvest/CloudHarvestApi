from CloudHarvestCoreTasks.blueprints import HarvestApiBlueprint
from flask import Response, jsonify
from logging import getLogger

from .home import not_implemented_error

logger = getLogger('harvest')


users_blueprint = HarvestApiBlueprint(
    'users_bp', __name__
)

@users_blueprint.route(rule='/list', methods=['GET'])
def list() -> Response:
    """
    Lists all users.
    :return: A response.
    """
    return not_implemented_error()


def lookup_user_by_token(token: str) -> str:
    """
    Looks up a user by their token. Tokens are stored in the Redis `harvest-tokens` Silo.
    :param token: The token to look up.
    :return: The username.
    """

    from CloudHarvestCoreTasks.silos import get_silo

    silo = get_silo('harvest-tokens')

    connection = silo.connect()

    result = connection.hget(name=token, key='username')

    if result:
        return result
