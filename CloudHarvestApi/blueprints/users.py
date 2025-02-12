from CloudHarvestCoreTasks.blueprints import HarvestApiBlueprint
from flask import Response
from logging import getLogger

from .base import safe_jsonify
from .home import not_implemented_error

logger = getLogger('harvest')


users_blueprint = HarvestApiBlueprint(
    'users_bp', __name__
)

@users_blueprint.route(rule='/list', methods=['GET'])
def list_users() -> Response:
    """
    Lists all users.
    :return: A response.
    """
    from CloudHarvestCoreTasks.silos import get_silo
    silo = get_silo('harvest-users')

    # Returns a MongoClient object
    client = silo.connect()

    result = client[silo.database]['users'].find()

    return safe_jsonify(
        success=bool(result),
        reason='OK' if result else 'No users found',
        result=list(result)
    )

@users_blueprint.route(rule='/lookup_by_token/<token>', methods=['GET'])
def lookup_user_by_token(token: str) -> Response:
    """
    Looks up a user by their token. Tokens are stored in the Redis `harvest-tokens` Silo.
    :param token: The token to look up.
    :return: The username.
    """

    return not_implemented_error()
