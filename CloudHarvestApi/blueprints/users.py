from CloudHarvestCoreTasks.blueprints import HarvestApiBlueprint
from flask import Response, jsonify
from logging import getLogger

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

    return jsonify({
        'success': bool(result),
        'message': 'No users found' if not result else 'OK',
        'result': result
    })

@users_blueprint.route(rule='/lookup_by_token/<token>', methods=['GET'])
def lookup_user_by_token(token: str) -> Response:
    """
    Looks up a user by their token. Tokens are stored in the Redis `harvest-tokens` Silo.
    :param token: The token to look up.
    :return: The username.
    """

    # TODO: Implement this method and remove the not_implemented_error() call
    return not_implemented_error()

    # from CloudHarvestCoreTasks.silos import get_silo
    #
    # silo = get_silo('harvest-tokens')
    #
    # connection = silo.connect()
    #
    # result = connection.hget(name=token, key='username')
    #
    # if result:
    #     return result
